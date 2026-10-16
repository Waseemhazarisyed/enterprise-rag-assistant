import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user_id
from app.db.database import SessionLocal
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.message import Message
from app.models.rag_log import RAGLog
from app.services.embedding_service import create_embedding
from app.services.rag_service import (
    generate_grounded_answer,
    rewrite_question_for_retrieval,
)
from app.services.retrieval_service import search_similar_chunks


router = APIRouter()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# =========================================================
# CREATE CONVERSATION
# =========================================================

@router.post("/conversations")
def create_conversation(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    conversation = Conversation(
        user_id=user_id,
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return {
        "id": conversation.id,
        "created_at": conversation.created_at,
    }


# =========================================================
# SEND MESSAGE
# =========================================================

@router.post(
    "/conversations/{conversation_id}/messages"
)
def send_message(
    conversation_id: int,
    question: str,
    document_id: int | None = None,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    total_start = time.time()

    # -----------------------------------
    # VERIFY CONVERSATION OWNERSHIP
    # -----------------------------------

    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    # -----------------------------------
    # VERIFY DOCUMENT OWNERSHIP
    # -----------------------------------

    if document_id is not None:
        document = (
            db.query(Document)
            .filter(
                Document.id == document_id,
                Document.user_id == user_id,
            )
            .first()
        )

        if not document:
            raise HTTPException(
                status_code=404,
                detail="Document not found.",
            )

    # -----------------------------------
    # LOAD PREVIOUS CONVERSATION HISTORY
    # -----------------------------------

    previous_messages = (
        db.query(Message)
        .filter(
            Message.conversation_id
            == conversation_id
        )
        .order_by(
            Message.created_at.asc()
        )
        .all()
    )

    conversation_history = [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in previous_messages
    ]

    # -----------------------------------
    # SAVE CURRENT USER MESSAGE
    # -----------------------------------

    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=question,
    )

    db.add(user_message)
    db.commit()

    try:
        # -----------------------------------
        # 1. QUERY REWRITING
        # -----------------------------------

        rewritten_question = (
            rewrite_question_for_retrieval(
                question=question,
                conversation_history=conversation_history,
            )
        )

        print(
            "Original question:",
            question,
        )

        print(
            "Rewritten question:",
            rewritten_question,
        )

        print(
            "Selected document_id:",
            document_id,
        )

        print(
            "Authenticated user_id:",
            user_id,
        )

        # -----------------------------------
        # 2. EMBEDDING
        # -----------------------------------

        embedding_start = time.time()

        question_embedding = create_embedding(
            rewritten_question
        )

        embedding_latency_ms = round(
            (
                time.time()
                - embedding_start
            )
            * 1000,
            2,
        )

        # -----------------------------------
        # 3. RETRIEVAL
        #
        # Only retrieve chunks belonging
        # to the authenticated user.
        # -----------------------------------

        retrieval_start = time.time()

        results = search_similar_chunks(
            db=db,
            query_embedding=question_embedding,
            top_k=5,
            document_id=document_id,
            user_id=user_id,
        )

        retrieval_latency_ms = round(
            (
                time.time()
                - retrieval_start
            )
            * 1000,
            2,
        )

        context_chunks = [
            result["chunk"].content
            for result in results
        ]

        # -----------------------------------
        # 4. LLM ANSWER
        # -----------------------------------

        llm_start = time.time()

        answer = generate_grounded_answer(
            question=question,
            context_chunks=context_chunks,
            conversation_history=conversation_history,
        )

        llm_latency_ms = round(
            (
                time.time()
                - llm_start
            )
            * 1000,
            2,
        )

        # -----------------------------------
        # 5. SAVE ASSISTANT RESPONSE
        # -----------------------------------

        assistant_message = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=answer,
        )

        db.add(assistant_message)

        # -----------------------------------
        # 6. CALCULATE METRICS
        # -----------------------------------

        total_latency_ms = round(
            (
                time.time()
                - total_start
            )
            * 1000,
            2,
        )

        top_similarity = (
            results[0]["similarity"]
            if results
            else None
        )

        # -----------------------------------
        # 7. SAVE RAG LOG
        #
        # IMPORTANT:
        # Save the authenticated user_id.
        # -----------------------------------

        rag_log = RAGLog(
            user_id=user_id,
            question=question,
            answer=answer,
            top_similarity=top_similarity,
            embedding_latency_ms=embedding_latency_ms,
            retrieval_latency_ms=retrieval_latency_ms,
            llm_latency_ms=llm_latency_ms,
            total_latency_ms=total_latency_ms,
            status="success",
        )

        db.add(rag_log)

        db.commit()

        db.refresh(
            assistant_message
        )

        db.refresh(
            rag_log
        )

        # -----------------------------------
        # 8. RETURN RESPONSE
        # -----------------------------------

        return {
            "conversation_id":
                conversation_id,

            "question":
                question,

            "rewritten_question":
                rewritten_question,

            "document_id":
                document_id,

            "answer":
                answer,

            "log_id":
                rag_log.id,

            "top_similarity":
                top_similarity,

            "latency_ms": {
                "embedding":
                    embedding_latency_ms,

                "retrieval":
                    retrieval_latency_ms,

                "llm":
                    llm_latency_ms,

                "total":
                    total_latency_ms,
            },

            "retrieval": [
                {
                    "chunk_id":
                        result["chunk"].id,

                    "document_id":
                        result[
                            "chunk"
                        ].document_id,

                    "page_number":
                        result[
                            "chunk"
                        ].page_number,

                    "chunk_index":
                        result[
                            "chunk"
                        ].chunk_index,

                    "similarity":
                        result[
                            "similarity"
                        ],
                }
                for result in results
            ],
        }

    except HTTPException:
        raise

    except Exception as error:
        db.rollback()

        total_latency_ms = round(
            (
                time.time()
                - total_start
            )
            * 1000,
            2,
        )

        try:
            # -----------------------------------
            # SAVE FAILED RAG LOG
            #
            # Also attach the user_id.
            # -----------------------------------

            failed_log = RAGLog(
                user_id=user_id,
                question=question,
                answer=None,
                top_similarity=None,
                embedding_latency_ms=None,
                retrieval_latency_ms=None,
                llm_latency_ms=None,
                total_latency_ms=total_latency_ms,
                status="failed",
                error_message=str(error),
            )

            db.add(failed_log)
            db.commit()

        except Exception as log_error:
            db.rollback()

            print(
                "Failed to save error log:",
                log_error,
            )

        print(
            "Conversation RAG error:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to generate answer.",
        )


# =========================================================
# GET CONVERSATION
# =========================================================

@router.get(
    "/conversations/{conversation_id}"
)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    # -----------------------------------
    # VERIFY CONVERSATION OWNERSHIP
    # -----------------------------------

    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id
            == conversation_id,

            Conversation.user_id
            == user_id,
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    # -----------------------------------
    # LOAD MESSAGES
    # -----------------------------------

    messages = (
        db.query(Message)
        .filter(
            Message.conversation_id
            == conversation_id
        )
        .order_by(
            Message.created_at.asc()
        )
        .all()
    )

    return {
        "conversation_id":
            conversation.id,

        "created_at":
            conversation.created_at,

        "messages": [
            {
                "id":
                    message.id,

                "role":
                    message.role,

                "content":
                    message.content,

                "created_at":
                    message.created_at,
            }
            for message in messages
        ],
    }
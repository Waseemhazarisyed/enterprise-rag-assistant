import time

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.document import Document
from app.models.rag_log import RAGLog
from app.services.embedding_service import create_embedding
from app.services.rag_service import generate_grounded_answer
from app.services.retrieval_service import search_similar_chunks

router = APIRouter()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/chat")
def chat(
    question: str,
    db: Session = Depends(get_db),
):
    total_start = time.time()

    # 1. Embedding
    embedding_start = time.time()

    question_embedding = create_embedding(question)

    embedding_latency_ms = round(
        (time.time() - embedding_start) * 1000,
        2,
    )

    # 2. Retrieval
    retrieval_start = time.time()

    results = search_similar_chunks(
        db=db,
        query_embedding=question_embedding,
        top_k=5,
    )

    retrieval_latency_ms = round(
        (time.time() - retrieval_start) * 1000,
        2,
    )

    context_chunks = [
        result["chunk"].content
        for result in results
    ]

    # 3. LLM generation
    llm_start = time.time()

    answer = generate_grounded_answer(
        question=question,
        context_chunks=context_chunks,
    )

    llm_latency_ms = round(
        (time.time() - llm_start) * 1000,
        2,
    )

    # 4. Build sources
    sources = []
    seen_sources = set()

    for result in results:
        chunk = result["chunk"]
        similarity = result["similarity"]

        document = (
            db.query(Document)
            .filter(Document.id == chunk.document_id)
            .first()
        )

        filename = document.filename if document else "Unknown"
        source_key = (filename, chunk.page_number)

        if source_key not in seen_sources:
            seen_sources.add(source_key)

            sources.append(
                {
                    "filename": filename,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    "similarity": similarity,
                }
            )

    # 5. Total latency
    total_latency_ms = round(
        (time.time() - total_start) * 1000,
        2,
    )

    # 6. Get strongest retrieval score
    top_similarity = (
        results[0]["similarity"]
        if results
        else None
    )

    # 7. Save observability log to PostgreSQL
    rag_log = RAGLog(
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
    db.refresh(rag_log)

    # 8. Return API response
    return {
        "question": question,
        "answer": answer,
        "latency_ms": {
            "embedding": embedding_latency_ms,
            "retrieval": retrieval_latency_ms,
            "llm": llm_latency_ms,
            "total": total_latency_ms,
        },
        "top_similarity": top_similarity,
        "log_id": rag_log.id,
        "sources": sources,
    }
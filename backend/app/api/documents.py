import hashlib
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.auth import get_current_user_id
from app.db.database import SessionLocal
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.chunking_service import chunk_text
from app.services.embedding_service import create_embedding
from app.services.pdf_parser import extract_pdf_text
from app.services.storage_service import (
    delete_pdf,
    download_pdf,
    upload_pdf,
)

router = APIRouter()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# =========================================================
# UPLOAD DOCUMENT
# =========================================================

@router.post("/documents")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported right now.",
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded PDF is empty.",
        )

    # -----------------------------------
    # 1. CREATE FILE HASH
    # -----------------------------------

    file_hash = hashlib.sha256(
        file_bytes
    ).hexdigest()

    # -----------------------------------
    # 2. DUPLICATE CHECK
    #
    # Only check duplicates belonging
    # to THIS logged-in user.
    # -----------------------------------

    existing_document = (
        db.query(Document)
        .filter(
            Document.user_id == user_id,
            Document.file_hash == file_hash,
        )
        .first()
    )

    if existing_document:
        raise HTTPException(
            status_code=409,
            detail="You have already uploaded this document.",
        )

    # -----------------------------------
    # 3. CREATE USER-SPECIFIC STORAGE PATH
    # -----------------------------------

    original_filename = (
        file.filename or "document.pdf"
    )

    unique_filename = (
        f"{uuid.uuid4()}-{original_filename}"
    )

    storage_path = (
        f"{user_id}/{unique_filename}"
    )

    # Example:
    #
    # Documents/
    #   abc-user-id/
    #       uuid-handbook.pdf

    # -----------------------------------
    # 4. UPLOAD ORIGINAL PDF TO SUPABASE
    # -----------------------------------

    try:
        upload_pdf(
            storage_path=storage_path,
            file_bytes=file_bytes,
        )

    except Exception as error:
        print(
            "Supabase upload error:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to upload PDF to cloud storage.",
        )

    try:
        # -----------------------------------
        # 5. EXTRACT TEXT
        # -----------------------------------

        pages = extract_pdf_text(
            file_bytes
        )

        if not pages:
            raise ValueError(
                "No readable text was found in the PDF."
            )

        # -----------------------------------
        # 6. CREATE DOCUMENT RECORD
        #
        # IMPORTANT:
        # Save the authenticated user_id.
        # -----------------------------------

        document = Document(
            user_id=user_id,
            filename=original_filename,
            file_type=(
                file.content_type
                or "application/pdf"
            ),
            status="parsed",
            file_hash=file_hash,
            storage_path=storage_path,
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        # -----------------------------------
        # 7. CHUNK + EMBED + SAVE
        # -----------------------------------

        chunks_created = 0

        for page in pages:
            page_chunks = chunk_text(
                page["text"]
            )

            for chunk_index, chunk in enumerate(
                page_chunks
            ):
                embedding = create_embedding(
                    chunk
                )

                document_chunk = DocumentChunk(
                    document_id=document.id,
                    content=chunk,
                    page_number=page[
                        "page_number"
                    ],
                    chunk_index=chunk_index,
                    embedding=embedding,
                )

                db.add(
                    document_chunk
                )

                chunks_created += 1

        db.commit()

        return {
            "id": document.id,
            "filename": document.filename,
            "file_type": document.file_type,
            "status": document.status,
            "storage_path": document.storage_path,
            "pages_extracted": len(pages),
            "chunks_created": chunks_created,
            "preview": (
                pages[0]["text"][:300]
                if pages
                else ""
            ),
        }

    except HTTPException:
        raise

    except Exception as error:
        db.rollback()

        # If processing failed after the
        # cloud upload, clean up the file.
        try:
            delete_pdf(
                storage_path
            )

        except Exception as storage_error:
            print(
                "Failed to clean up Supabase file:",
                storage_error,
            )

        print(
            "Document processing error:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to process the uploaded PDF.",
        )


# =========================================================
# LIST DOCUMENTS
# =========================================================

@router.get("/documents")
def list_documents(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    documents = (
        db.query(Document)
        .filter(
            Document.user_id == user_id
        )
        .order_by(
            Document.created_at.desc()
        )
        .all()
    )

    return [
        {
            "id": document.id,
            "filename": document.filename,
            "file_type": document.file_type,
            "status": document.status,
            "storage_path": document.storage_path,
            "created_at": document.created_at,
        }
        for document in documents
    ]


# =========================================================
# DELETE DOCUMENT
# =========================================================

@router.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    # IMPORTANT:
    # Match BOTH document ID and user ID.
    #
    # A user cannot delete another
    # user's document by guessing its ID.

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
    # DELETE CLOUD PDF
    # -----------------------------------

    if document.storage_path:
        try:
            delete_pdf(
                document.storage_path
            )

        except Exception as error:
            print(
                "Supabase delete error:",
                error,
            )

            raise HTTPException(
                status_code=500,
                detail="Failed to delete PDF from cloud storage.",
            )

    # -----------------------------------
    # DELETE DATABASE RECORD
    # -----------------------------------

    db.delete(document)
    db.commit()

    return {
        "message":
            "Document deleted successfully",
        "document_id":
            document_id,
    }


# =========================================================
# REPROCESS DOCUMENT
# =========================================================

@router.post(
    "/documents/{document_id}/reprocess"
)
def reprocess_document(
    document_id: int,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    # Again:
    # document must belong to THIS user.

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

    if not document.storage_path:
        raise HTTPException(
            status_code=400,
            detail=(
                "This document does not have "
                "a cloud storage path."
            ),
        )

    # -----------------------------------
    # 1. DOWNLOAD FROM SUPABASE
    # -----------------------------------

    try:
        file_bytes = download_pdf(
            document.storage_path
        )

    except Exception as error:
        print(
            "Supabase download error:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to download original "
                "PDF from cloud storage."
            ),
        )

    # -----------------------------------
    # 2. EXTRACT TEXT
    # -----------------------------------

    pages = extract_pdf_text(
        file_bytes
    )

    # -----------------------------------
    # 3. DELETE OLD CHUNKS
    # -----------------------------------

    (
        db.query(DocumentChunk)
        .filter(
            DocumentChunk.document_id
            == document.id
        )
        .delete()
    )

    chunks_created = 0

    # -----------------------------------
    # 4. RECREATE CHUNKS + EMBEDDINGS
    # -----------------------------------

    for page in pages:
        page_chunks = chunk_text(
            page["text"]
        )

        for chunk_index, chunk in enumerate(
            page_chunks
        ):
            embedding = create_embedding(
                chunk
            )

            document_chunk = DocumentChunk(
                document_id=document.id,
                content=chunk,
                page_number=page[
                    "page_number"
                ],
                chunk_index=chunk_index,
                embedding=embedding,
            )

            db.add(
                document_chunk
            )

            chunks_created += 1

    document.status = "parsed"

    db.commit()

    return {
        "message":
            "Document reprocessed successfully",
        "document_id":
            document.id,
        "filename":
            document.filename,
        "storage_path":
            document.storage_path,
        "pages_extracted":
            len(pages),
        "chunks_created":
            chunks_created,
    }
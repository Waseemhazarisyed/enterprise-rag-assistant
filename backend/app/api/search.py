from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.services.embedding_service import create_embedding
from app.services.retrieval_service import search_similar_chunks

router = APIRouter()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/search")
def search_documents(
    query: str,
    db: Session = Depends(get_db),
):
    query_embedding = create_embedding(query)

    results = search_similar_chunks(
        db=db,
        query_embedding=query_embedding,
        top_k=5,
    )

    return [
        {
            "id": result["chunk"].id,
            "document_id": result["chunk"].document_id,
            "page_number": result["chunk"].page_number,
            "chunk_index": result["chunk"].chunk_index,
            "content": result["chunk"].content,
            "similarity": result["similarity"],
            "distance": result["distance"],
        }
        for result in results
    ]
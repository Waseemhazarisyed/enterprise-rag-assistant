from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.document_chunk import DocumentChunk


def search_similar_chunks(
    db: Session,
    query_embedding: list[float],
    top_k: int = 5,
    document_id: int | None = None,
    user_id: str | None = None,
):
    distance = (
        DocumentChunk.embedding.cosine_distance(
            query_embedding
        )
    )

    query = (
        db.query(
            DocumentChunk,
            distance.label("distance"),
        )
        .join(
            Document,
            DocumentChunk.document_id
            == Document.id,
        )
    )

    # -----------------------------------
    # USER ISOLATION
    # -----------------------------------

    if user_id is not None:
        query = query.filter(
            Document.user_id == user_id
        )

    # -----------------------------------
    # OPTIONAL DOCUMENT FILTER
    # -----------------------------------

    if document_id is not None:
        query = query.filter(
            DocumentChunk.document_id
            == document_id
        )

    results = (
        query
        .order_by(distance)
        .limit(top_k)
        .all()
    )

    return [
        {
            "chunk": chunk,
            "distance": float(
                distance_value
            ),
            "similarity": round(
                1 - float(
                    distance_value
                ),
                4,
            ),
        }
        for chunk, distance_value
        in results
    ]
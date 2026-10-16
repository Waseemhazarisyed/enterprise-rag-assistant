from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth import get_current_user_id
from app.db.database import SessionLocal
from app.models.rag_log import RAGLog

router = APIRouter()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/metrics/summary")
def metrics_summary(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    total_requests = (
        db.query(func.count(RAGLog.id))
        .filter(
            RAGLog.user_id == user_id
        )
        .scalar()
        or 0
    )

    successful_requests = (
        db.query(func.count(RAGLog.id))
        .filter(
            RAGLog.user_id == user_id,
            RAGLog.status == "success",
        )
        .scalar()
        or 0
    )

    failed_requests = (
        db.query(func.count(RAGLog.id))
        .filter(
            RAGLog.user_id == user_id,
            RAGLog.status == "failed",
        )
        .scalar()
        or 0
    )

    averages = (
        db.query(
            func.avg(
                RAGLog.embedding_latency_ms
            ),
            func.avg(
                RAGLog.retrieval_latency_ms
            ),
            func.avg(
                RAGLog.llm_latency_ms
            ),
            func.avg(
                RAGLog.total_latency_ms
            ),
            func.avg(
                RAGLog.top_similarity
            ),
        )
        .filter(
            RAGLog.user_id == user_id
        )
        .first()
    )

    return {
        "total_requests":
            total_requests,

        "successful_requests":
            successful_requests,

        "failed_requests":
            failed_requests,

        "average_embedding_latency_ms":
            round(
                float(
                    averages[0] or 0
                ),
                2,
            ),

        "average_retrieval_latency_ms":
            round(
                float(
                    averages[1] or 0
                ),
                2,
            ),

        "average_llm_latency_ms":
            round(
                float(
                    averages[2] or 0
                ),
                2,
            ),

        "average_total_latency_ms":
            round(
                float(
                    averages[3] or 0
                ),
                2,
            ),

        "average_top_similarity":
            round(
                float(
                    averages[4] or 0
                ),
                4,
            ),
    }
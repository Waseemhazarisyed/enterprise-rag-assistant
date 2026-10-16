from sqlalchemy import Column, DateTime, Float, Integer, String, Text, func

from app.db.database import Base


class RAGLog(Base):
    __tablename__ = "rag_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        String,
        nullable=True,
        index=True,
    )

    question = Column(
        Text,
        nullable=False,
    )

    answer = Column(
        Text,
        nullable=True,
    )

    top_similarity = Column(
        Float,
        nullable=True,
    )

    embedding_latency_ms = Column(
        Float,
        nullable=True,
    )

    retrieval_latency_ms = Column(
        Float,
        nullable=True,
    )

    llm_latency_ms = Column(
        Float,
        nullable=True,
    )

    total_latency_ms = Column(
        Float,
        nullable=True,
    )

    status = Column(
        String,
        nullable=False,
        default="success",
    )

    error_message = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
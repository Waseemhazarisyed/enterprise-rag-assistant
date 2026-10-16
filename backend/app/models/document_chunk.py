from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, func
from pgvector.sqlalchemy import Vector

from app.db.database import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)

    document_id = Column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )

    content = Column(Text, nullable=False)

    page_number = Column(Integer, nullable=True)

    chunk_index = Column(Integer, nullable=False)

    embedding = Column(Vector(1536), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
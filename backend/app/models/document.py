from sqlalchemy import Column, DateTime, Integer, String, func

from app.db.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        String,
        nullable=True,
        index=True,
    )

    filename = Column(
        String,
        nullable=False,
    )

    file_type = Column(
        String,
        nullable=False,
    )

    status = Column(
        String,
        nullable=False,
        default="uploaded",
    )

    file_hash = Column(
        String,
        unique=True,
        index=True,
        nullable=True,
    )

    storage_path = Column(
        String,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
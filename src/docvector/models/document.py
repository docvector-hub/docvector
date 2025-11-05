"""Document model - indexed documents."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class Document(Base, UUIDMixin, TimestampMixin):
    """
    Document metadata and content.

    Represents a single document that has been fetched and indexed.
    """

    __tablename__ = "documents"

    # Foreign keys
    source_id: Mapped[UUID] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Document identification
    url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True, index=True)
    path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Content
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_length: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Metadata (flexible JSON)
    metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    format: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Processing status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending", index=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Chunking info
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    chunking_strategy: Mapped[str] = mapped_column(String(50), default="semantic")

    # Timestamps
    fetched_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # External metadata
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    modified_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationships
    source = relationship("Source", back_populates="documents")
    chunks = relationship(
        "Chunk",
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name="valid_document_status",
        ),
        Index("idx_documents_source_url", "source_id", "url", unique=True, postgresql_where="url IS NOT NULL"),
        Index("idx_documents_created_desc", created_at.desc()),
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title='{self.title}', status='{self.status}')>"

"""Chunk model - document chunks for vector search."""

from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class Chunk(Base, UUIDMixin, TimestampMixin):
    """
    Document chunk.

    Represents a chunk of a document that will be embedded and indexed
    for vector search.
    """

    __tablename__ = "chunks"

    # Foreign keys
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Chunk identification
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_length: Mapped[int] = mapped_column(Integer, nullable=False)

    # Context preservation
    heading_hierarchy: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    previous_chunk_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("chunks.id", ondelete="SET NULL"),
        nullable=True,
    )
    next_chunk_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("chunks.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Metadata
    metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Position in document
    start_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    end_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Embedding info
    has_embedding: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    embedding_model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    vector_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )

    # Relationships
    document = relationship("Document", back_populates="chunks")
    previous_chunk = relationship(
        "Chunk",
        foreign_keys=[previous_chunk_id],
        remote_side="Chunk.id",
        uselist=False,
    )
    next_chunk = relationship(
        "Chunk",
        foreign_keys=[next_chunk_id],
        remote_side="Chunk.id",
        uselist=False,
    )

    # Indexes
    __table_args__ = (
        Index("idx_chunks_doc_index", "document_id", "chunk_index", unique=True),
    )

    def __repr__(self) -> str:
        return f"<Chunk(id={self.id}, document_id={self.document_id}, index={self.chunk_index})>"

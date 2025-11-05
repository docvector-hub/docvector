"""Source model - documentation source configurations."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin


class Source(Base, UUIDMixin, TimestampMixin):
    """
    Documentation source configuration.

    A source represents a location from which documents are fetched
    (website, git repo, file upload, API, etc.)
    """

    __tablename__ = "sources"

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="active", index=True
    )

    # Configuration (flexible JSON)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Authentication (encrypted at application level)
    auth_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Crawling/fetching settings
    max_depth: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    max_pages: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    respect_robots_txt: Mapped[bool] = mapped_column(Boolean, default=True)

    # Scheduling
    sync_frequency: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    next_sync_at: Mapped[Optional[datetime]] = mapped_column(nullable=True, index=True)

    # Metadata
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Statistics (updated by triggers/background jobs)
    total_documents: Mapped[int] = mapped_column(Integer, default=0)
    total_chunks: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    documents = relationship(
        "Document",
        back_populates="source",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    jobs = relationship(
        "IngestionJob",
        back_populates="source",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "type IN ('web', 'git', 'file', 'api')",
            name="valid_source_type",
        ),
        CheckConstraint(
            "status IN ('active', 'paused', 'error')",
            name="valid_source_status",
        ),
    )

    def __repr__(self) -> str:
        return f"<Source(id={self.id}, name='{self.name}', type='{self.type}')>"

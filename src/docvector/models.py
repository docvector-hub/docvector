"""SQLAlchemy database models."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class Source(Base):
    """Source model - represents a documentation source."""

    __tablename__ = "sources"

    id: UUID = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: str = Column(String(255), nullable=False, unique=True)
    type: str = Column(String(50), nullable=False)
    config: dict = Column(JSONB, nullable=False, server_default="{}")
    status: str = Column(String(50), nullable=False, server_default="active")
    sync_frequency: Optional[str] = Column(String(50), nullable=True)
    last_synced_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    error_message: Optional[str] = Column(Text, nullable=True)
    created_at: datetime = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: datetime = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    documents = relationship("Document", back_populates="source", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Source(id={self.id}, name={self.name}, type={self.type})>"


class Document(Base):
    """Document model - represents a single document from a source."""

    __tablename__ = "documents"

    id: UUID = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id: UUID = Column(
        PG_UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    url: Optional[str] = Column(String(2048), nullable=True)
    path: Optional[str] = Column(String(1024), nullable=True)
    content_hash: str = Column(String(64), nullable=False)
    title: Optional[str] = Column(String(512), nullable=True)
    content: Optional[str] = Column(Text, nullable=True)
    content_length: Optional[int] = Column(Integer, nullable=True)
    metadata_: dict = Column("metadata", JSONB, nullable=False, server_default="{}")
    language: str = Column(String(10), nullable=False, server_default="en")
    format: Optional[str] = Column(String(50), nullable=True)
    status: str = Column(String(50), nullable=False, server_default="pending")
    error_message: Optional[str] = Column(Text, nullable=True)
    chunk_count: int = Column(Integer, server_default="0")
    chunking_strategy: str = Column(String(50), server_default="semantic")
    fetched_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    processed_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    author: Optional[str] = Column(String(255), nullable=True)
    published_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    modified_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    created_at: datetime = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: datetime = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    source = relationship("Source", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title={self.title}, status={self.status})>"


class Chunk(Base):
    """Chunk model - represents a chunk of a document."""

    __tablename__ = "chunks"

    id: UUID = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: UUID = Column(
        PG_UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    index: int = Column(Integer, nullable=False)
    content: str = Column(Text, nullable=False)
    content_length: int = Column(Integer, nullable=False)
    start_char: Optional[int] = Column(Integer, nullable=True)
    end_char: Optional[int] = Column(Integer, nullable=True)
    metadata_: dict = Column("metadata", JSONB, nullable=False, server_default="{}")
    embedding_id: Optional[str] = Column(String(255), nullable=True)
    embedding_model: Optional[str] = Column(String(255), nullable=True)
    embedded_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    created_at: datetime = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: datetime = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    document = relationship("Document", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<Chunk(id={self.id}, document_id={self.document_id}, index={self.index})>"


class Job(Base):
    """Job model - represents a background job."""

    __tablename__ = "jobs"

    id: UUID = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id: Optional[UUID] = Column(
        PG_UUID(as_uuid=True), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True
    )
    type: str = Column(String(50), nullable=False)
    status: str = Column(String(50), nullable=False, server_default="pending")
    progress: dict = Column(JSONB, nullable=False, server_default="{}")
    result: Optional[dict] = Column(JSONB, nullable=True)
    error_message: Optional[str] = Column(Text, nullable=True)
    started_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    completed_at: Optional[datetime] = Column(DateTime(timezone=True), nullable=True)
    created_at: datetime = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: datetime = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, type={self.type}, status={self.status})>"

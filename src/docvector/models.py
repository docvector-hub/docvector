"""SQLAlchemy database models."""

from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class Library(Base):
    """Library model - represents a software library/package."""

    __tablename__ = "libraries"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    library_id = Column(String(255), nullable=False, unique=True)  # e.g., "mongodb/docs", "vercel/next.js"
    name = Column(String(255), nullable=False)  # Human-readable name
    description = Column(Text, nullable=True)
    homepage_url = Column(String(2048), nullable=True)
    repository_url = Column(String(2048), nullable=True)
    aliases = Column(ARRAY(String), nullable=False, server_default="{}")  # Alternative names
    metadata_ = Column("metadata", JSONB, nullable=False, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    sources = relationship("Source", back_populates="library")

    def __repr__(self) -> str:
        return f"<Library(id={self.id}, library_id={self.library_id}, name={self.name})>"


class Source(Base):
    """Source model - represents a documentation source."""

    __tablename__ = "sources"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, unique=True)
    type = Column(String(50), nullable=False)
    library_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("libraries.id", ondelete="SET NULL"), nullable=True
    )
    version = Column(String(50), nullable=True)  # Library version (e.g., "3.11", "18.2.0")
    config = Column(JSONB, nullable=False, server_default="{}")
    status = Column(String(50), nullable=False, server_default="active")
    sync_frequency = Column(String(50), nullable=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    library = relationship("Library", back_populates="sources")
    documents = relationship("Document", back_populates="source", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Source(id={self.id}, name={self.name}, type={self.type}, version={self.version})>"


class Document(Base):
    """Document model - represents a single document from a source."""

    __tablename__ = "documents"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    url = Column(String(2048), nullable=True)
    path = Column(String(1024), nullable=True)
    content_hash = Column(String(64), nullable=False)
    title = Column(String(512), nullable=True)
    content = Column(Text, nullable=True)
    content_length = Column(Integer, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=False, server_default="{}")
    language = Column(String(10), nullable=False, server_default="en")
    format = Column(String(50), nullable=True)
    status = Column(String(50), nullable=False, server_default="pending")
    error_message = Column(Text, nullable=True)
    chunk_count = Column(Integer, server_default="0")
    chunking_strategy = Column(String(50), server_default="semantic")
    fetched_at = Column(DateTime(timezone=True), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    author = Column(String(255), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    modified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    source = relationship("Source", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title={self.title}, status={self.status})>"


class Chunk(Base):
    """Chunk model - represents a chunk of a document."""

    __tablename__ = "chunks"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    content_length = Column(Integer, nullable=False)
    start_char = Column(Integer, nullable=True)
    end_char = Column(Integer, nullable=True)

    # Context7-style features
    is_code_snippet = Column(Integer, nullable=False, server_default="0")  # Boolean (0/1)
    code_language = Column(String(50), nullable=True)  # Programming language
    topics = Column(ARRAY(String), nullable=False, server_default="{}")  # Topic tags
    enrichment = Column(Text, nullable=True)  # LLM-generated explanation

    # Quality scores (0-1 range)
    relevance_score = Column(Float, nullable=True)  # Question relevance
    code_quality_score = Column(Float, nullable=True)  # Code quality
    formatting_score = Column(Float, nullable=True)  # Formatting quality
    metadata_score = Column(Float, nullable=True)  # Metadata richness
    initialization_score = Column(Float, nullable=True)  # Initialization guidance

    metadata_ = Column("metadata", JSONB, nullable=False, server_default="{}")
    embedding_id = Column(String(255), nullable=True)
    embedding_model = Column(String(255), nullable=True)
    embedded_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    document = relationship("Document", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<Chunk(id={self.id}, document_id={self.document_id}, index={self.index})>"


class Job(Base):
    """Job model - represents a background job."""

    __tablename__ = "jobs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id = Column(
        PG_UUID(as_uuid=True), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True
    )
    type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, server_default="pending")
    progress = Column(JSONB, nullable=False, server_default="{}")
    result = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, type={self.type}, status={self.status})>"

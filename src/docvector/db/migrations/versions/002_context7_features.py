"""Add Context7-style features: libraries, versions, code snippets, reranking scores.

Revision ID: 002
Revises: 001
Create Date: 2025-11-17

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create libraries table
    op.create_table(
        "libraries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("library_id", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("homepage_url", sa.String(2048), nullable=True),
        sa.Column("repository_url", sa.String(2048), nullable=True),
        sa.Column(
            "aliases",
            postgresql.ARRAY(sa.String),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("metadata", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Add library_id and version columns to sources table
    op.add_column(
        "sources",
        sa.Column("library_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "sources",
        sa.Column("version", sa.String(50), nullable=True),
    )

    # Add foreign key constraint
    op.create_foreign_key(
        "fk_sources_library_id",
        "sources",
        "libraries",
        ["library_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Add Context7-style fields to chunks table
    op.add_column(
        "chunks",
        sa.Column("is_code_snippet", sa.Integer, nullable=False, server_default="0"),
    )
    op.add_column(
        "chunks",
        sa.Column("code_language", sa.String(50), nullable=True),
    )
    op.add_column(
        "chunks",
        sa.Column(
            "topics",
            postgresql.ARRAY(sa.String),
            nullable=False,
            server_default="{}",
        ),
    )
    op.add_column(
        "chunks",
        sa.Column("enrichment", sa.Text(), nullable=True),
    )

    # Add quality score columns to chunks table
    op.add_column(
        "chunks",
        sa.Column("relevance_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "chunks",
        sa.Column("code_quality_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "chunks",
        sa.Column("formatting_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "chunks",
        sa.Column("metadata_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "chunks",
        sa.Column("initialization_score", sa.Float(), nullable=True),
    )

    # Create indexes for better query performance
    op.create_index(
        "idx_libraries_library_id",
        "libraries",
        ["library_id"],
    )
    op.create_index(
        "idx_sources_library_id",
        "sources",
        ["library_id"],
    )
    op.create_index(
        "idx_sources_version",
        "sources",
        ["version"],
    )
    op.create_index(
        "idx_chunks_is_code_snippet",
        "chunks",
        ["is_code_snippet"],
    )
    op.create_index(
        "idx_chunks_code_language",
        "chunks",
        ["code_language"],
    )

    # Create GIN index for topics array (for fast array searches)
    op.execute(
        "CREATE INDEX idx_chunks_topics ON chunks USING GIN (topics)"
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop indexes
    op.drop_index("idx_chunks_topics")
    op.drop_index("idx_chunks_code_language")
    op.drop_index("idx_chunks_is_code_snippet")
    op.drop_index("idx_sources_version")
    op.drop_index("idx_sources_library_id")
    op.drop_index("idx_libraries_library_id")

    # Drop columns from chunks table
    op.drop_column("chunks", "initialization_score")
    op.drop_column("chunks", "metadata_score")
    op.drop_column("chunks", "formatting_score")
    op.drop_column("chunks", "code_quality_score")
    op.drop_column("chunks", "relevance_score")
    op.drop_column("chunks", "enrichment")
    op.drop_column("chunks", "topics")
    op.drop_column("chunks", "code_language")
    op.drop_column("chunks", "is_code_snippet")

    # Drop foreign key and columns from sources table
    op.drop_constraint("fk_sources_library_id", "sources", type_="foreignkey")
    op.drop_column("sources", "version")
    op.drop_column("sources", "library_id")

    # Drop libraries table
    op.drop_table("libraries")

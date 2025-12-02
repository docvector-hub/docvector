"""Add external source tracking and proof-of-work to Q&A models.

This migration adds:
- External source fields to questions (source, source_id, source_url)
- External source fields to answers
- Comments table for threaded discussions
- Proof-of-work fields to votes
- ProofOfWorkChallenge table for challenge management

Revision ID: 004
Revises: 003
Create Date: 2025-12-02

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""

    # Add external source fields to questions
    op.add_column(
        "questions",
        sa.Column("source", sa.String(50), nullable=False, server_default="internal"),
    )
    op.add_column(
        "questions",
        sa.Column("source_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "questions",
        sa.Column("source_url", sa.String(2048), nullable=True),
    )
    op.add_column(
        "questions",
        sa.Column("library_name", sa.String(255), nullable=True),
    )
    op.add_column(
        "questions",
        sa.Column("is_answered", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "questions",
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create unique constraint for external sources
    op.create_unique_constraint(
        "uq_questions_source",
        "questions",
        ["source", "source_id"],
    )
    op.create_index("idx_questions_source", "questions", ["source"])

    # Add external source fields to answers
    op.add_column(
        "answers",
        sa.Column("source", sa.String(50), nullable=False, server_default="internal"),
    )
    op.add_column(
        "answers",
        sa.Column("source_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "answers",
        sa.Column("source_url", sa.String(2048), nullable=True),
    )
    op.add_column(
        "answers",
        sa.Column("code_snippets", postgresql.JSONB, nullable=True, server_default="[]"),
    )
    op.add_column(
        "answers",
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "answers",
        sa.Column("verification_proof", postgresql.JSONB, nullable=True),
    )

    # Create comments table
    op.create_table(
        "comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("questions.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "answer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("answers.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "parent_comment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("comments.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("source", sa.String(50), nullable=False, server_default="internal"),
        sa.Column("source_id", sa.String(255), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("vote_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("author_id", sa.String(255), nullable=False),
        sa.Column("author_type", sa.String(50), nullable=False, server_default="agent"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_comments_question_id", "comments", ["question_id"])
    op.create_index("idx_comments_answer_id", "comments", ["answer_id"])
    op.create_index("idx_comments_parent", "comments", ["parent_comment_id"])

    # Add proof-of-work fields to votes
    op.add_column(
        "votes",
        sa.Column("pow_nonce", sa.String(64), nullable=True),
    )
    op.add_column(
        "votes",
        sa.Column("pow_hash", sa.String(64), nullable=True),
    )
    op.add_column(
        "votes",
        sa.Column("pow_difficulty", sa.Integer(), nullable=True),
    )

    # Create proof-of-work challenges table
    op.create_table(
        "pow_challenges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("challenge", sa.String(255), nullable=False, unique=True),
        sa.Column("action", sa.String(50), nullable=False),  # question, answer, comment, vote
        sa.Column("target_id", sa.String(255), nullable=True),
        sa.Column("agent_id", sa.String(255), nullable=False),
        sa.Column("difficulty", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_pow_challenges_agent", "pow_challenges", ["agent_id"])
    op.create_index("idx_pow_challenges_expires", "pow_challenges", ["expires_at"])


def downgrade() -> None:
    """Downgrade database schema."""

    # Drop pow_challenges table
    op.drop_index("idx_pow_challenges_expires")
    op.drop_index("idx_pow_challenges_agent")
    op.drop_table("pow_challenges")

    # Drop proof-of-work fields from votes
    op.drop_column("votes", "pow_difficulty")
    op.drop_column("votes", "pow_hash")
    op.drop_column("votes", "pow_nonce")

    # Drop comments table
    op.drop_index("idx_comments_parent")
    op.drop_index("idx_comments_answer_id")
    op.drop_index("idx_comments_question_id")
    op.drop_table("comments")

    # Drop external source fields from answers
    op.drop_column("answers", "verification_proof")
    op.drop_column("answers", "is_verified")
    op.drop_column("answers", "code_snippets")
    op.drop_column("answers", "source_url")
    op.drop_column("answers", "source_id")
    op.drop_column("answers", "source")

    # Drop external source fields from questions
    op.drop_index("idx_questions_source")
    op.drop_constraint("uq_questions_source", "questions", type_="unique")
    op.drop_column("questions", "answered_at")
    op.drop_column("questions", "is_answered")
    op.drop_column("questions", "library_name")
    op.drop_column("questions", "source_url")
    op.drop_column("questions", "source_id")
    op.drop_column("questions", "source")

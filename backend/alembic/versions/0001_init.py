"""init

Revision ID: 0001_init
Revises:
Create Date: 2026-04-07
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "calls",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("language", sa.String(length=32), nullable=False),
        sa.Column("duration", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "transcripts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("call_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("speaker", sa.String(length=32), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("start_time", sa.Float(), nullable=False),
        sa.Column("end_time", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["call_id"], ["calls.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "insights",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("call_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("objections", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("action_items", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("sentiment_timeline", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("call_score", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["call_id"], ["calls.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("call_id"),
    )


def downgrade() -> None:
    op.drop_table("insights")
    op.drop_table("transcripts")
    op.drop_table("calls")

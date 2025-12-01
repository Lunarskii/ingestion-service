"""create chat sources tables

Revision ID: f2b9e2e48467
Revises: ebbae282a8cc
Create Date: 2025-08-20 18:18:34.291592

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f2b9e2e48467"
down_revision: Union[str, Sequence[str], None] = "ebbae282a8cc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "retrieval_sources",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("message_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("source_type", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["chat_messages.id"],
            name=op.f("retrieval_sources_message_id_chat_messages_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("retrieval_sources_pkey")),
    )
    op.create_table(
        "retrieval_chunks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("retrieval_source_id", sa.Integer(), nullable=False),
        sa.Column("chunk_id", sa.String(), nullable=False),
        sa.Column("page_start", sa.BigInteger(), nullable=False),
        sa.Column("page_end", sa.BigInteger(), nullable=False),
        sa.Column("retrieval_score", sa.Float(), nullable=False),
        sa.Column("reranked_score", sa.Float(), nullable=True),
        sa.Column("combined_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["retrieval_source_id"],
            ["retrieval_sources.id"],
            name=op.f("retrieval_chunks_retrieval_source_id_retrieval_sources_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("retrieval_chunks_pkey")),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table("retrieval_chunks")
    op.drop_table("retrieval_sources")

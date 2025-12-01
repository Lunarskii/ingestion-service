"""create topics tables

Revision ID: 7e008f52ea43
Revises: f703949fefef
Create Date: 2025-09-28 14:31:00.350518

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7e008f52ea43"
down_revision: Union[str, Sequence[str], None] = "f703949fefef"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "topics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("topics_pkey")),
        sa.UniqueConstraint("code", name=op.f("topics_code_key")),
    )
    op.create_table(
        "document_topics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.BigInteger(), nullable=False),
        sa.Column(
            "source",
            sa.Enum(
                "rules",
                "ml",
                "manual",
                name="topic_source",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("document_topics_document_id_documents_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"],
            ["topics.id"],
            name=op.f("document_topics_topic_id_topics_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("document_topics_pkey")),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table("document_topics")
    op.drop_table("topics")

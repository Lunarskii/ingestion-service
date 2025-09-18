"""create documents table

Revision ID: 198a886ed4a8
Revises: f2b9e2e48467
Create Date: 2025-08-23 14:58:27.322365

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "198a886ed4a8"
down_revision: Union[str, Sequence[str], None] = "f2b9e2e48467"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("workspace_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("media_type", sa.String(), nullable=False),
        sa.Column("detected_language", sa.String(), nullable=True),
        sa.Column("page_count", sa.BigInteger(), nullable=True),
        sa.Column("author", sa.String(), nullable=True),
        sa.Column("creation_date", sa.DateTime(), nullable=True),
        sa.Column("raw_storage_path", sa.String(), nullable=False),
        sa.Column("silver_storage_path", sa.String(), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("ingested_at", sa.DateTime(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "QUEUED",
                "RUNNING",
                "EXTRACTING",
                "CHUNKING",
                "EMBEDDING",
                "SUCCESS",
                "FAILED",
                name="document_status",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("documents_pkey")),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table("documents")

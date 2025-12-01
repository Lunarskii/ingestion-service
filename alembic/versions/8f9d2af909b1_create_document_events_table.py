"""create document events table

Revision ID: 8f9d2af909b1
Revises: 7e008f52ea43
Create Date: 2025-10-03 00:47:26.567225

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "8f9d2af909b1"
down_revision: Union[str, Sequence[str], None] = "7e008f52ea43"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "document_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("trace_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column(
            "stage",
            sa.Enum(
                "EXTRACTING",
                "CHUNKING",
                "EMBEDDING",
                "CLASSIFICATION",
                "LANG_DETECT",
                name="document_stage",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "QUEUED",
                "PROCESSING",
                "SUCCESS",
                "FAILED",
                "SKIPPED",
                name="document_status",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("document_events_pkey")),
        sa.UniqueConstraint("document_id", "stage", name="uq_document_events_document_id_stage"),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table("document_events")

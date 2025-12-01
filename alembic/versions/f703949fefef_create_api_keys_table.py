"""create api_keys table

Revision ID: f703949fefef
Revises: 198a886ed4a8
Create Date: 2025-09-22 13:52:58.866093

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f703949fefef"
down_revision: Union[str, Sequence[str], None] = "198a886ed4a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("key_hash", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("api_keys_pkey")),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table("api_keys")

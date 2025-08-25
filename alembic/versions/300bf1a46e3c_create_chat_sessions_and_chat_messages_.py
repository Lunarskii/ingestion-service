"""create chat sessions and chat messages table

Revision ID: 300bf1a46e3c
Revises:
Create Date: 2025-08-01 14:57:09.022297

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "300bf1a46e3c"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("workspace_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("chat_sessions_pkey")),
    )
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column("session_id", sa.Uuid(as_uuid=False), nullable=False),
        sa.Column(
            "role", sa.Enum("user", "assistant", name="chat_role", native_enum=False),
            nullable=False,
        ),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["chat_sessions.id"],
            name=op.f("chat_messages_session_id_chat_sessions_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("chat_messages_pkey")),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")

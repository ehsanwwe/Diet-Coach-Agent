"""add_chat_message_status_and_client_id

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-29

Additive changes — safe for existing SQLite rows:
- chat_messages: add status (pending|completed|failed), client_message_id, error_message
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chat_messages",
        sa.Column("status", sa.String(20), nullable=False, server_default="completed"),
    )
    op.add_column(
        "chat_messages",
        sa.Column("client_message_id", sa.String(64), nullable=True),
    )
    op.add_column(
        "chat_messages",
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_chat_messages_client_id",
        "chat_messages",
        ["session_id", "client_message_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_chat_messages_client_id", table_name="chat_messages")
    op.drop_column("chat_messages", "error_message")
    op.drop_column("chat_messages", "client_message_id")
    op.drop_column("chat_messages", "status")

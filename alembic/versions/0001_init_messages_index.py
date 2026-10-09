"""init messages index

Revision ID: 0001_init_messages_index
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_init_messages_index"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("route", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.String(),
            server_default=sa.func.current_timestamp(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_messages_session_id_id",
        "messages",
        ["session_id", "id"],
        unique=False,
        sqlite_where=None,
    )


def downgrade() -> None:
    op.drop_index("idx_messages_session_id_id", table_name="messages")
    op.drop_table("messages")

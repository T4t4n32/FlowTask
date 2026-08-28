"""initial: tabla tasks

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-28
"""
import sqlalchemy as sa

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("is_habit", sa.Boolean(), nullable=True),
        sa.Column("completed", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tasks_id", "tasks", ["id"])


def downgrade() -> None:
    op.drop_index("ix_tasks_id", table_name="tasks")
    op.drop_table("tasks")

"""tasks.due_at + tasks.reminder_sent

Revision ID: 0005_due_at
Revises: 0004_rls
Create Date: 2026-08-29
"""
import sqlalchemy as sa

from alembic import op

revision = "0005_due_at"
down_revision = "0004_rls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("due_at", sa.DateTime(), nullable=True))
    op.add_column(
        "tasks",
        sa.Column(
            "reminder_sent",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_index("ix_tasks_due_pending", "tasks", ["due_at", "reminder_sent"])


def downgrade() -> None:
    op.drop_index("ix_tasks_due_pending", table_name="tasks")
    op.drop_column("tasks", "reminder_sent")
    op.drop_column("tasks", "due_at")

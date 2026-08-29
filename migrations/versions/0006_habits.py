"""habits + tasks.habit_id

Revision ID: 0006_habits
Revises: 0005_due_at
Create Date: 2026-08-29
"""
import sqlalchemy as sa

from alembic import op

revision = "0006_habits"
down_revision = "0005_due_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "habits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("target_time", sa.Time(), nullable=True),
        sa.Column(
            "active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_habits_user"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_habits_id", "habits", ["id"])
    op.create_index("ix_habits_user_active", "habits", ["user_id", "active"])

    with op.batch_alter_table("tasks") as batch:
        batch.add_column(sa.Column("habit_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_tasks_habit", "habits", ["habit_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("tasks") as batch:
        batch.drop_constraint("fk_tasks_habit", type_="foreignkey")
        batch.drop_column("habit_id")
    op.drop_index("ix_habits_user_active", table_name="habits")
    op.drop_index("ix_habits_id", table_name="habits")
    op.drop_table("habits")

"""users + tasks.user_id

Revision ID: 0002_users
Revises: 0001_initial
Create Date: 2026-08-29

Nota: asume que `tasks` está vacía (se añade user_id como NOT NULL sin backfill).
"""
import sqlalchemy as sa

from alembic import op

revision = "0002_users"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("platform", sa.String(), nullable=False),
        sa.Column("chat_id", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("platform", "chat_id", name="uq_users_platform_chat"),
    )
    op.create_index("ix_users_id", "users", ["id"])

    # batch_alter_table => SQLite hace copy/recreate; en Postgres son ALTERs normales.
    with op.batch_alter_table("tasks") as batch:
        batch.add_column(sa.Column("user_id", sa.Integer(), nullable=False))
        batch.create_foreign_key("fk_tasks_user", "users", ["user_id"], ["id"])
        batch.create_index("ix_tasks_user_created", ["user_id", "created_at"])


def downgrade() -> None:
    with op.batch_alter_table("tasks") as batch:
        batch.drop_index("ix_tasks_user_created")
        batch.drop_constraint("fk_tasks_user", type_="foreignkey")
        batch.drop_column("user_id")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")

"""sessions (token de la PWA)

Revision ID: 0008_sessions
Revises: 0007_projects
Create Date: 2026-08-29
"""
import sqlalchemy as sa

from alembic import op

revision = "0008_sessions"
down_revision = "0007_projects"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("last_seen", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_sessions_user"),
        sa.PrimaryKeyConstraint("token"),
    )


def downgrade() -> None:
    op.drop_table("sessions")

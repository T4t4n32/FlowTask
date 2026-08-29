"""projects + tasks.project_id

Revision ID: 0007_projects
Revises: 0006_habits
Create Date: 2026-08-29
"""
import sqlalchemy as sa

from alembic import op

revision = "0007_projects"
down_revision = "0006_habits"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("rubric", sa.Text(), nullable=True),
        sa.Column("deadline", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_projects_user"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], name="fk_projects_team"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_projects_id", "projects", ["id"])

    with op.batch_alter_table("tasks") as batch:
        batch.add_column(sa.Column("project_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_tasks_project", "projects", ["project_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("tasks") as batch:
        batch.drop_constraint("fk_tasks_project", type_="foreignkey")
        batch.drop_column("project_id")
    op.drop_index("ix_projects_id", table_name="projects")
    op.drop_table("projects")

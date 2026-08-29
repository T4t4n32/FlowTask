"""teams + team_members + tasks.team_id/assignee_id

Revision ID: 0003_teams
Revises: 0002_users
Create Date: 2026-08-29
"""
import sqlalchemy as sa

from alembic import op

revision = "0003_teams"
down_revision = "0002_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("invite_code", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], name="fk_teams_owner"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_teams_id", "teams", ["id"])
    op.create_index("uq_teams_invite_code", "teams", ["invite_code"], unique=True)

    op.create_table(
        "team_members",
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("joined_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], name="fk_team_members_team"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_team_members_user"),
        sa.PrimaryKeyConstraint("team_id", "user_id"),
    )

    with op.batch_alter_table("tasks") as batch:
        batch.add_column(sa.Column("team_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("assignee_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_tasks_team", "teams", ["team_id"], ["id"])
        batch.create_foreign_key("fk_tasks_assignee", "users", ["assignee_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("tasks") as batch:
        batch.drop_constraint("fk_tasks_assignee", type_="foreignkey")
        batch.drop_constraint("fk_tasks_team", type_="foreignkey")
        batch.drop_column("assignee_id")
        batch.drop_column("team_id")
    op.drop_table("team_members")
    op.drop_index("uq_teams_invite_code", table_name="teams")
    op.drop_index("ix_teams_id", table_name="teams")
    op.drop_table("teams")

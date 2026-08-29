"""Habilita Row Level Security (deny-by-default) en las tablas de datos

Revision ID: 0004_rls
Revises: 0003_teams
Create Date: 2026-08-29

RLS es solo Postgres/Supabase (no-op en SQLite).

Estrategia: ENABLE ROW LEVEL SECURITY sin políticas permisivas.
- Los roles `anon` / `authenticated` (API auto-generada de Supabase, SDKs con JWT)
  ven CERO filas y no pueden escribir.
- El backend de FlowTask conecta como `postgres` (dueño de las tablas) y **bypasea RLS
  a propósito**: la barrera primaria es el filtrado por `user_id` en la API.
- NO se usa FORCE ROW LEVEL SECURITY (rompería al backend).
- Las políticas reales por usuario (`auth.uid()`) llegan en la Task 15/16, cuando
  `users` gane una columna `auth_uid` ligada a Supabase Auth.
"""
from alembic import op

revision = "0004_rls"
down_revision = "0003_teams"
branch_labels = None
depends_on = None

_TABLES = ("users", "tasks", "teams", "team_members")


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    for tbl in _TABLES:
        op.execute(f"ALTER TABLE {tbl} ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    for tbl in _TABLES:
        op.execute(f"ALTER TABLE {tbl} DISABLE ROW LEVEL SECURITY")

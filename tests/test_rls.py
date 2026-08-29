"""Task 6: RLS deny-by-default. Opt-in — hace red contra Postgres, no corre por defecto.

Cómo correrlo:  RLS_TEST=1 venv/Scripts/pytest tests/test_rls.py
Necesita DATABASE_URL (en .env o en el entorno) apuntando a Postgres/Supabase.
Todo ocurre dentro de una transacción que se revierte: no toca datos reales.
"""
import os

import pytest
from dotenv import dotenv_values
from sqlalchemy import create_engine, text

# .env primero: los tests de SQLite ensucian os.environ["DATABASE_URL"] al importarse.
_URL = (
    dotenv_values(".env").get("DATABASE_URL")
    or os.environ.get("DATABASE_URL")
    or ""
).strip()

pytestmark = pytest.mark.skipif(
    os.environ.get("RLS_TEST") != "1" or not _URL.startswith("postgresql"),
    reason="RLS: fija RLS_TEST=1 y DATABASE_URL de Postgres para correrlo",
)


def _engine():
    url = _URL.replace("postgresql://", "postgresql+psycopg://", 1)
    return create_engine(url, connect_args={"prepare_threshold": None})


def test_rls_bloquea_lectura_a_authenticated():
    """Con RLS activo y sin política permisiva, `authenticated` no ve filas
    aunque tenga el privilegio SELECT."""
    with _engine().connect() as c:
        trans = c.begin()
        try:
            c.execute(text("GRANT SELECT ON tasks TO authenticated"))
            c.execute(
                text("INSERT INTO users (platform, chat_id) VALUES ('rlstest', 'rlstest')")
            )
            uid = c.execute(
                text("SELECT id FROM users WHERE platform = 'rlstest'")
            ).scalar()
            c.execute(
                text(
                    "INSERT INTO tasks (user_id, title, category) "
                    "VALUES (:u, 'fila rls', 'TASK')"
                ),
                {"u": uid},
            )

            # como dueño (postgres) la fila existe
            assert c.execute(text("SELECT count(*) FROM tasks")).scalar() >= 1

            # como authenticated: RLS sin política => 0 filas
            c.execute(text("SET LOCAL ROLE authenticated"))
            assert c.execute(text("SELECT count(*) FROM tasks")).scalar() == 0
            c.execute(text("RESET ROLE"))
        finally:
            trans.rollback()  # revierte grant + inserts + set role


def test_backend_owner_bypasa_rls():
    """El rol por defecto (el que usa el backend) sigue leyendo/escribiendo."""
    with _engine().connect() as c:
        trans = c.begin()
        try:
            for tbl in ("users", "tasks", "teams", "team_members"):
                c.execute(text(f"SELECT count(*) FROM {tbl}"))
            c.execute(
                text("INSERT INTO users (platform, chat_id) VALUES ('rlstest2', 'x')")
            )
            assert c.execute(
                text("SELECT count(*) FROM users WHERE platform = 'rlstest2'")
            ).scalar() == 1
        finally:
            trans.rollback()

"""BD de test compartida + limpieza entre tests.

Se fija DATABASE_URL antes de importar el paquete (config.load_dotenv no la pisa).
Cada test arranca con las tablas vacías.
"""
import os
import pathlib

_DB = pathlib.Path(__file__).parent / "test_flowtask.db"
_DB.unlink(missing_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{_DB.as_posix()}"

import pytest  # noqa: E402

from src.flowtask.infrastructure.database import (  # noqa: E402
    Base,
    SessionLocal,
    init_db,
)

init_db()  # aplica todas las migraciones una vez


@pytest.fixture(autouse=True)
def _clean_db():
    yield
    db = SessionLocal()
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()
    db.close()

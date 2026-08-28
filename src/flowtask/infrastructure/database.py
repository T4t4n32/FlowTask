from datetime import datetime
from pathlib import Path

from sqlalchemy import Boolean, Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from ..config import settings

# Supabase entrega la URL como "postgresql://..."; SQLAlchemy necesita el driver explícito.
DATABASE_URL = settings.DATABASE_URL
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

_IS_SQLITE = DATABASE_URL.startswith("sqlite")

if _IS_SQLITE:
    _engine_kwargs = {"connect_args": {"check_same_thread": False}}
else:
    # Transaction pooler de Supabase (puerto 6543): sin prepared statements con nombre,
    # pool chico para no agotar el límite de conexiones.
    _engine_kwargs = {
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 2,
        "connect_args": {"prepare_threshold": None},
    }

engine = create_engine(DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

_ROOT = Path(__file__).resolve().parents[3]


class TaskModel(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    category = Column(String)
    is_habit = Column(Boolean, default=False)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)


def init_db():
    """Aplica las migraciones pendientes. Equivale a `alembic upgrade head`."""
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(_ROOT / "migrations"))
    cfg.attributes["configure_logger"] = False
    command.upgrade(cfg, "head")


def save_to_db(ai_res):
    db = SessionLocal()
    new_item = TaskModel(
        title=ai_res.clean_title,
        category=ai_res.category,
        is_habit=ai_res.is_habit,
        completed=False
    )
    db.add(new_item)
    db.commit()
    db.close()

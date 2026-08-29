from datetime import datetime
from pathlib import Path

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Time,
    UniqueConstraint,
    create_engine,
    text,
)
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


class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, nullable=False)       # "telegram", luego "whatsapp"
    chat_id = Column(String, nullable=False)        # id de chat en esa plataforma
    display_name = Column(String)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("platform", "chat_id", name="uq_users_platform_chat"),
    )


class TeamModel(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    invite_code = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        Index("uq_teams_invite_code", "invite_code", unique=True),
    )


class TeamMemberModel(Base):
    __tablename__ = "team_members"
    team_id = Column(Integer, ForeignKey("teams.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    role = Column(String, nullable=False)          # "owner" | "member"
    joined_at = Column(DateTime, default=datetime.now)


class HabitModel(Base):
    """Definición de un hábito recurrente. Cada día genera una instancia en `tasks`."""
    __tablename__ = "habits"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    target_time = Column(Time, nullable=True)   # hora del día para el recordatorio (None = sin hora)
    active = Column(Boolean, nullable=False, server_default=text("true"), default=True)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (Index("ix_habits_user_active", "user_id", "active"),)


class TaskModel(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=True)
    title = Column(String)
    category = Column(String)
    is_habit = Column(Boolean, default=False)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    due_at = Column(DateTime, nullable=True)                 # cuándo recordar (None = sin recordatorio)
    reminder_sent = Column(
        Boolean, nullable=False, server_default=text("false"), default=False
    )

    __table_args__ = (
        Index("ix_tasks_user_created", "user_id", "created_at"),
        Index("ix_tasks_due_pending", "due_at", "reminder_sent"),
    )


def init_db():
    """Aplica las migraciones pendientes. Equivale a `alembic upgrade head`."""
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(_ROOT / "migrations"))
    cfg.attributes["configure_logger"] = False
    command.upgrade(cfg, "head")


def get_or_create_user(platform: str, chat_id, display_name: str = "") -> int:
    """Devuelve el id del usuario para (platform, chat_id), creándolo si no existe."""
    db = SessionLocal()
    try:
        chat_id = str(chat_id)
        user = (
            db.query(UserModel)
            .filter(UserModel.platform == platform, UserModel.chat_id == chat_id)
            .first()
        )
        if user is None:
            user = UserModel(
                platform=platform, chat_id=chat_id, display_name=display_name
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user.id
    finally:
        db.close()


def save_to_db(ai_res, user_id: int, due_at=None):
    db = SessionLocal()
    new_item = TaskModel(
        user_id=user_id,
        title=ai_res.clean_title,
        category=ai_res.category,
        is_habit=ai_res.is_habit,
        completed=False,
        due_at=due_at,
    )
    db.add(new_item)
    db.commit()
    db.close()

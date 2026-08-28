import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

from ..config import settings

DATABASE_URL = settings.DATABASE_URL

# check_same_thread es exclusivo de SQLite; en Postgres rompe.
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TaskModel(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    category = Column(String)
    is_habit = Column(Boolean, default=False)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

def init_db():
    # Si la BD es SQLite en una subcarpeta, crearla antes de conectar.
    if DATABASE_URL.startswith("sqlite"):
        db_path = DATABASE_URL.replace("sqlite:///", "").lstrip("/")
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    Base.metadata.create_all(bind=engine)

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
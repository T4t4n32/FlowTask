import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./flowtask.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TaskModel(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    category = Column(String)
    is_habit = Column(Boolean, default=False)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.now)

def init_db():
    Base.metadata.create_all(bind=engine)

def save_to_db(ai_res):
    db = SessionLocal()
    new_task = TaskModel(
        title=ai_res.clean_title,
        category=ai_res.category,
        is_habit=ai_res.is_habit,
        completed=False,
        created_at=datetime.datetime.now()
    )
    db.add(new_task)
    db.commit()
    db.close()
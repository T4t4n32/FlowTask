"""Hábitos recurrentes: alta y generación de la instancia diaria en `tasks`."""
import logging
from datetime import date, datetime, time

from sqlalchemy import func

from .infrastructure.database import HabitModel, SessionLocal, TaskModel

logger = logging.getLogger(__name__)


def _ensure_today_instance(db, habit: HabitModel, today: date) -> bool:
    """Crea la tarea de hoy para el hábito si aún no existe. Devuelve True si la creó."""
    exists = (
        db.query(TaskModel)
        .filter(
            TaskModel.habit_id == habit.id,
            func.date(TaskModel.created_at) == today,
        )
        .first()
    )
    if exists:
        return False
    due_at = (
        datetime.combine(today, habit.target_time)
        if habit.target_time is not None
        else None
    )
    db.add(
        TaskModel(
            user_id=habit.user_id,
            habit_id=habit.id,
            title=habit.title,
            category="HABIT",
            is_habit=True,
            due_at=due_at,
        )
    )
    return True


def create_habit(user_id: int, title: str, target_time: time | None) -> dict:
    """Da de alta el hábito y genera ya su instancia de hoy."""
    db = SessionLocal()
    try:
        habit = HabitModel(user_id=user_id, title=title.strip(), target_time=target_time)
        db.add(habit)
        db.flush()
        _ensure_today_instance(db, habit, date.today())
        db.commit()
        return {"id": habit.id, "title": habit.title, "target_time": target_time}
    finally:
        db.close()


def rollover_habits() -> int:
    """Genera la instancia de hoy para cada hábito activo. Idempotente. Devuelve cuántas creó."""
    db = SessionLocal()
    created = 0
    try:
        today = date.today()
        for habit in db.query(HabitModel).filter(HabitModel.active == True).all():  # noqa: E712
            if _ensure_today_instance(db, habit, today):
                created += 1
        db.commit()
    except Exception as e:
        logger.error("Falla en rollover_habits: %s", e)
    finally:
        db.close()
    return created

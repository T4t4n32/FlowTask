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


def list_habits(user_id: int) -> list[dict]:
    db = SessionLocal()
    try:
        rows = (
            db.query(HabitModel)
            .filter(HabitModel.user_id == user_id)
            .order_by(HabitModel.id)
            .all()
        )
        return [
            {"id": h.id, "title": h.title, "target_time": h.target_time, "active": h.active}
            for h in rows
        ]
    finally:
        db.close()


def set_active(habit_id: int, user_id: int, active: bool) -> str | None:
    db = SessionLocal()
    try:
        h = db.query(HabitModel).filter_by(id=habit_id, user_id=user_id).first()
        if h is None:
            return None
        h.active = active
        db.commit()
        return h.title
    finally:
        db.close()


def delete_habit(habit_id: int, user_id: int) -> str | None:
    """Borra el hábito y sus tareas de hoy aún pendientes."""
    db = SessionLocal()
    try:
        h = db.query(HabitModel).filter_by(id=habit_id, user_id=user_id).first()
        if h is None:
            return None
        title = h.title
        db.query(TaskModel).filter(
            TaskModel.habit_id == habit_id, TaskModel.completed == False  # noqa: E712
        ).delete()
        db.delete(h)
        db.commit()
        return title
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

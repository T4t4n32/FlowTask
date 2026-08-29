"""Barrido de recordatorios: cada 60s manda avisos de tareas vencidas."""
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .infrastructure.database import SessionLocal, TaskModel, UserModel
from .messaging import send_message

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def reminder_sweep() -> None:
    """Tareas con due_at vencido, no avisadas y no completadas → recordatorio."""
    db = SessionLocal()
    try:
        due = (
            db.query(TaskModel)
            .filter(
                TaskModel.due_at.isnot(None),
                TaskModel.due_at <= datetime.now(),
                TaskModel.reminder_sent == False,  # noqa: E712
                TaskModel.completed == False,      # noqa: E712
            )
            .all()
        )
        for task in due:
            user = db.get(UserModel, task.assignee_id or task.user_id)
            if user is None:
                continue
            text = f"⏰ *Recordatorio:* {task.title}"
            if await send_message(user.platform, user.chat_id, text):
                task.reminder_sent = True  # solo si el envío fue OK
                db.commit()
    except Exception as e:
        logger.error("Falla en reminder_sweep: %s", e)
    finally:
        db.close()


def start() -> None:
    # ponytail: max_instances=1 basta con 1 réplica; con varias → pg_advisory_lock aquí.
    scheduler.add_job(
        reminder_sweep,
        "interval",
        seconds=60,
        id="reminder_sweep",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info("Scheduler arrancado (reminder_sweep cada 60s)")


def shutdown() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)

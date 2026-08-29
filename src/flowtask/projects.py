"""Proyectos: persistir una meta + las tareas que genera la IA."""
from datetime import date, datetime, time

from .infrastructure.ai_engine import GeneratedTask
from .infrastructure.database import ProjectModel, SessionLocal, TaskModel

_HABIT_HOUR = time(9, 0)  # hora por defecto de recordatorio de una tarea de proyecto


def create_project(
    user_id: int,
    title: str,
    rubric: str,
    deadline: date,
    tasks: list[GeneratedTask],
    team_id: int | None = None,
) -> dict:
    """Crea el proyecto y una fila en `tasks` por cada tarea generada."""
    db = SessionLocal()
    try:
        project = ProjectModel(
            user_id=user_id,
            team_id=team_id,
            title=title.strip(),
            rubric=rubric or None,
            deadline=deadline,
        )
        db.add(project)
        db.flush()
        for gt in tasks:
            db.add(
                TaskModel(
                    user_id=user_id,
                    team_id=team_id,
                    project_id=project.id,
                    title=gt.title,
                    category="TASK",
                    due_at=datetime.combine(gt.due_date, _HABIT_HOUR),
                )
            )
        db.commit()
        return {"id": project.id, "title": project.title, "n_tasks": len(tasks)}
    finally:
        db.close()


def list_projects(user_id: int) -> list[dict]:
    """Proyectos del usuario con su progreso (hechas / total)."""
    db = SessionLocal()
    try:
        rows = (
            db.query(ProjectModel)
            .filter(ProjectModel.user_id == user_id)
            .order_by(ProjectModel.deadline)
            .all()
        )
        out = []
        for p in rows:
            tasks = db.query(TaskModel).filter(TaskModel.project_id == p.id).all()
            done = sum(1 for t in tasks if t.completed)
            out.append(
                {
                    "id": p.id,
                    "title": p.title,
                    "deadline": p.deadline,
                    "done": done,
                    "total": len(tasks),
                }
            )
        return out
    finally:
        db.close()

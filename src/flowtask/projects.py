"""Proyectos: persistir una meta + las tareas que genera la IA."""
from datetime import date, datetime, time

from .infrastructure.ai_engine import GeneratedTask
from .infrastructure.database import (
    ProjectModel,
    SessionLocal,
    TaskModel,
    TeamMemberModel,
    UserModel,
)

_TASK_HOUR = time(9, 0)  # hora por defecto de recordatorio de una tarea de proyecto


def _balanced_assign(db, member_ids: list[int], tasks: list) -> dict:
    """Reparte tareas al miembro con menos carga pendiente. Devuelve {user_id: [tasks]}."""
    load = {
        uid: db.query(TaskModel)
        .filter(TaskModel.assignee_id == uid, TaskModel.completed == False)  # noqa: E712
        .count()
        for uid in member_ids
    }
    result = {uid: [] for uid in member_ids}
    for gt in tasks:
        winner = min(member_ids, key=lambda u: (load[u], u))
        load[winner] += 1
        result[winner].append(gt)
    return result


def create_project(
    user_id: int,
    title: str,
    rubric: str,
    deadline: date,
    tasks: list[GeneratedTask],
    team_id: int | None = None,
) -> dict:
    """Crea el proyecto y una fila en `tasks` por cada tarea generada.

    Si el proyecto es de equipo, reparte las tareas entre los miembros (equilibrando
    por carga) y devuelve `assignments` = {user_id: [títulos]} para notificar.
    """
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

        members = (
            [r.user_id for r in db.query(TeamMemberModel).filter_by(team_id=team_id).all()]
            if team_id is not None
            else []
        )
        assignments: dict[int, list[str]] = {}

        if members:
            for uid, gts in _balanced_assign(db, members, tasks).items():
                for gt in gts:
                    db.add(_task_row(gt, owner=uid, assignee=uid, team_id=team_id,
                                     project_id=project.id))
                if gts:
                    assignments[uid] = [gt.title for gt in gts]
        else:
            for gt in tasks:
                db.add(_task_row(gt, owner=user_id, assignee=None, team_id=team_id,
                                 project_id=project.id))

        db.commit()
        return {
            "id": project.id,
            "title": project.title,
            "n_tasks": len(tasks),
            "assignments": assignments,
        }
    finally:
        db.close()


def _task_row(gt, owner, assignee, team_id, project_id):
    return TaskModel(
        user_id=owner,
        assignee_id=assignee,
        team_id=team_id,
        project_id=project_id,
        title=gt.title,
        category="TASK",
        due_at=datetime.combine(gt.due_date, _TASK_HOUR),
    )


def find_by_name(user_id: int, name: str) -> dict | None:
    """Proyecto (propio o de un equipo del usuario) que coincide por nombre."""
    target = name.strip().lower()
    for p in list_projects(user_id):
        if p["title"].lower() == target:
            return p
    return None


def add_task(project_id: int, user_id: int, title: str, due_at=None) -> None:
    """Añade una tarea suelta a un proyecto existente ('Para X, hacer Y')."""
    db = SessionLocal()
    try:
        proj = db.get(ProjectModel, project_id)
        team_id = proj.team_id if proj else None
        db.add(
            TaskModel(
                user_id=user_id,
                assignee_id=user_id if team_id else None,
                team_id=team_id,
                project_id=project_id,
                title=title.strip() or "(sin título)",
                category="TASK",
                due_at=due_at,
            )
        )
        db.commit()
    finally:
        db.close()


def contacts_for(user_ids: list[int]) -> dict[int, tuple[str, str]]:
    """{user_id: (platform, chat_id)} para notificar."""
    db = SessionLocal()
    try:
        return {
            u.id: (u.platform, u.chat_id)
            for u in db.query(UserModel).filter(UserModel.id.in_(user_ids)).all()
        }
    finally:
        db.close()


def list_projects(user_id: int) -> list[dict]:
    """Proyectos del usuario con su progreso (hechas / total)."""
    db = SessionLocal()
    try:
        team_ids = [
            r.team_id
            for r in db.query(TeamMemberModel).filter_by(user_id=user_id).all()
        ]
        cond = ProjectModel.user_id == user_id
        if team_ids:
            cond = cond | ProjectModel.team_id.in_(team_ids)
        rows = (
            db.query(ProjectModel).filter(cond).order_by(ProjectModel.deadline).all()
        )
        names = {u.id: (u.display_name or f"user {u.id}") for u in db.query(UserModel).all()}
        out = []
        for p in rows:
            tasks = db.query(TaskModel).filter(TaskModel.project_id == p.id).all()
            done = sum(1 for t in tasks if t.completed)
            by_person = {}
            if p.team_id is not None:
                for t in tasks:
                    who = names.get(t.assignee_id, "sin asignar")
                    d, tot = by_person.get(who, (0, 0))
                    by_person[who] = (d + int(bool(t.completed)), tot + 1)
            out.append(
                {
                    "id": p.id,
                    "title": p.title,
                    "deadline": p.deadline,
                    "done": done,
                    "total": len(tasks),
                    "by_person": {k: f"{v[0]}/{v[1]}" for k, v in by_person.items()},
                }
            )
        return out
    finally:
        db.close()

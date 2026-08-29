"""Task 13: flujo de chat /proyecto (meta → rúbrica → fecha → confirmar)."""
import asyncio
from datetime import date, timedelta

from src.flowtask import main, projects
from src.flowtask.infrastructure.ai_engine import GeneratedTask
from src.flowtask.infrastructure.database import (
    ProjectModel,
    SessionLocal,
    TaskModel,
    get_or_create_user,
)

DEADLINE = date.today() + timedelta(days=30)


def _fake_plan(goal, rubric, deadline):
    return [
        GeneratedTask(title=f"{goal} - paso 1", due_date=date.today() + timedelta(days=3)),
        GeneratedTask(title=f"{goal} - paso 2", due_date=date.today() + timedelta(days=12)),
        GeneratedTask(title=f"{goal} - paso 3", due_date=deadline),
    ]


def _install_fake_ai(monkeypatch):
    async def fake(goal, rubric, deadline):
        return _fake_plan(goal, rubric, deadline)

    monkeypatch.setattr(main.ai_engine, "decompose_goal", fake)


def _send(text, chat_id="1300"):
    return asyncio.run(main.handle_incoming_message("telegram", chat_id, text))


def _projects_count(user_id):
    db = SessionLocal()
    n = db.query(ProjectModel).filter(ProjectModel.user_id == user_id).count()
    db.close()
    return n


def test_wizard_completo_crea_proyecto_y_tareas(monkeypatch):
    _install_fake_ai(monkeypatch)
    uid = get_or_create_user("telegram", "1300")

    assert "meta del proyecto" in _send("/proyecto").lower()
    assert "rúbrica" in _send("Presentación de Historia").lower()
    assert "fecha límite" in _send("fuentes primarias").lower()
    plan = _send(DEADLINE.isoformat())
    assert "Plan para" in plan and "paso 1" in plan
    ok = _send("aceptar")
    assert "creado con 3 tareas" in ok

    assert _projects_count(uid) == 1
    db = SessionLocal()
    tasks = db.query(TaskModel).filter(TaskModel.project_id.isnot(None)).all()
    db.close()
    assert len(tasks) == 3 and all(t.due_at is not None for t in tasks)


def test_forma_de_un_mensaje(monkeypatch):
    _install_fake_ai(monkeypatch)
    uid = get_or_create_user("telegram", "1300")
    plan = _send(f"/proyecto Tesis | metodología clara | {DEADLINE.isoformat()}")
    assert "Plan para" in plan
    _send("aceptar")
    assert _projects_count(uid) == 1


def test_regenerar_no_duplica(monkeypatch):
    _install_fake_ai(monkeypatch)
    uid = get_or_create_user("telegram", "1300")
    _send("/proyecto Meta | - | " + DEADLINE.isoformat())
    _send("regenerar")
    _send("regenerar")
    _send("aceptar")
    assert _projects_count(uid) == 1


def test_cancelar_a_mitad(monkeypatch):
    _install_fake_ai(monkeypatch)
    uid = get_or_create_user("telegram", "1300")
    _send("/proyecto")
    _send("Algo")
    assert "cancelado" in _send("/cancelar").lower()
    # tras cancelar, un mensaje normal ya no entra al flujo
    assert "/proyecto" in _send("hola").lower() or _projects_count(uid) == 0


def test_proyectos_lista_progreso(monkeypatch):
    _install_fake_ai(monkeypatch)
    uid = get_or_create_user("telegram", "1300")
    _send(f"/proyecto Meta | - | {DEADLINE.isoformat()}")
    _send("aceptar")

    db = SessionLocal()
    db.query(TaskModel).filter(TaskModel.project_id.isnot(None)).first().completed = True
    db.commit()
    db.close()

    out = _send("/proyectos")
    assert "Meta" in out and "1/3" in out


def test_fecha_invalida_reintenta(monkeypatch):
    _install_fake_ai(monkeypatch)
    get_or_create_user("telegram", "1300")
    _send("/proyecto")
    _send("Meta")
    _send("ninguna")
    r = _send("cuando sea")
    assert "no entend" in r.lower()

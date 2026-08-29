"""Feedback 2026-08-29: 'Para <proyecto>, <tarea>' añade a un proyecto existente."""
import asyncio
from datetime import date, timedelta

from src.flowtask import main, projects
from src.flowtask.infrastructure.ai_engine import AIResponse, GeneratedTask
from src.flowtask.infrastructure.database import (
    SessionLocal,
    TaskModel,
    get_or_create_user,
)

DEADLINE = date.today() + timedelta(days=20)


def _send(text, chat_id="1"):
    return asyncio.run(main.handle_incoming_message("telegram", chat_id, text))


def _mk_project(user_id, title="Ensayo"):
    return projects.create_project(
        user_id, title, "", DEADLINE,
        [GeneratedTask(title="x", due_date=date.today() + timedelta(days=1))],
    )


def test_para_proyecto_existente_adjunta_tarea():
    uid = get_or_create_user("telegram", "1")
    pid = _mk_project(uid, "Ensayo")["id"]

    r = _send("Para Ensayo, escribir la introducción")
    assert "Añadido a" in r and "Ensayo" in r

    db = SessionLocal()
    titles = [t.title for t in db.query(TaskModel).filter(TaskModel.project_id == pid).all()]
    db.close()
    assert "escribir la introducción" in titles


def test_para_con_fecha_limpia_el_titulo(monkeypatch):
    uid = get_or_create_user("telegram", "1")
    pid = _mk_project(uid, "Tesis")["id"]

    r = _send("Para Tesis, revisar fuentes mañana a las 10")
    assert "revisar fuentes" in r and "10:00" in r

    db = SessionLocal()
    row = db.query(TaskModel).filter(
        TaskModel.project_id == pid, TaskModel.title == "revisar fuentes"
    ).first()
    db.close()
    assert row is not None and row.due_at is not None


class _FakeAI:
    def __init__(self, resp):
        self.resp = resp

    async def classify_text(self, text):
        return self.resp


def test_para_sin_proyecto_cae_a_tarea_normal(monkeypatch):
    get_or_create_user("telegram", "1")
    monkeypatch.setattr(
        main, "ai_engine",
        _FakeAI(AIResponse(intent="SAVE", category="TASK", clean_title="comprar leche")),
    )
    r = _send("Para casa, comprar leche")
    assert "Registrado" in r and "comprar leche" in r

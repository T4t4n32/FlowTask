"""Task 12: decompose_goal + create_project."""
import asyncio
from datetime import date, datetime, timedelta

from src.flowtask import projects
from src.flowtask.infrastructure.ai_engine import AIEngine, GeneratedTask
from src.flowtask.infrastructure.database import (
    SessionLocal,
    TaskModel,
    get_or_create_user,
)

TODAY = date.today()
DEADLINE = TODAY + timedelta(days=21)


def _decompose(engine, goal="Presentación de Historia", rubric="fuentes primarias", deadline=DEADLINE):
    return asyncio.run(engine.decompose_goal(goal, rubric, deadline))


def test_usa_las_tareas_de_la_ia_y_las_ordena(monkeypatch):
    engine = AIEngine()

    async def fake(prompt):
        return {"tasks": [
            {"title": "Escribir conclusiones", "due_date": (TODAY + timedelta(days=18)).isoformat(), "note": "cierre"},
            {"title": "Investigar fuentes", "due_date": (TODAY + timedelta(days=3)).isoformat(), "note": "biblioteca"},
            {"title": "Borrador de diapositivas", "due_date": (TODAY + timedelta(days=10)).isoformat()},
        ]}

    monkeypatch.setattr(engine, "_call_gemini", fake)
    out = _decompose(engine)
    assert len(out) == 3
    assert [t.title for t in out][0] == "Investigar fuentes"      # ordenado por fecha
    assert all(TODAY <= t.due_date <= DEADLINE for t in out)


def test_clampa_fechas_fuera_de_rango(monkeypatch):
    engine = AIEngine()

    async def fake(prompt):
        return {"tasks": [
            {"title": "A", "due_date": "2020-01-01"},                       # pasado
            {"title": "B", "due_date": (DEADLINE + timedelta(days=30)).isoformat()},  # más allá
            {"title": "C", "due_date": (TODAY + timedelta(days=5)).isoformat()},
        ]}

    monkeypatch.setattr(engine, "_call_gemini", fake)
    out = _decompose(engine)
    assert all(TODAY <= t.due_date <= DEADLINE for t in out)


def test_fallback_si_la_ia_falla(monkeypatch):
    engine = AIEngine()

    async def boom(prompt):
        raise RuntimeError("sin red")

    monkeypatch.setattr(engine, "_call_gemini", boom)
    out = _decompose(engine)
    assert 2 <= len(out) <= 6
    assert all(TODAY <= t.due_date <= DEADLINE for t in out)
    assert all("hito" in t.title for t in out)


def test_fallback_si_la_ia_devuelve_pocas(monkeypatch):
    engine = AIEngine()

    async def fake(prompt):
        return {"tasks": [{"title": "unica", "due_date": (TODAY + timedelta(days=2)).isoformat()}]}

    monkeypatch.setattr(engine, "_call_gemini", fake)
    out = _decompose(engine)
    assert len(out) >= 2 and all("hito" in t.title for t in out)


def test_create_project_persiste_meta_y_tareas():
    uid = get_or_create_user("telegram", "1200")
    gts = [
        GeneratedTask(title="Paso 1", due_date=TODAY + timedelta(days=2)),
        GeneratedTask(title="Paso 2", due_date=TODAY + timedelta(days=9)),
    ]
    res = projects.create_project(uid, "Proyecto X", "rúbrica", DEADLINE, gts)
    assert res["n_tasks"] == 2

    db = SessionLocal()
    rows = db.query(TaskModel).filter(TaskModel.project_id == res["id"]).all()
    db.close()
    assert len(rows) == 2
    assert all(r.category == "TASK" and r.due_at is not None for r in rows)
    assert {r.title for r in rows} == {"Paso 1", "Paso 2"}


def test_list_projects_muestra_progreso():
    uid = get_or_create_user("telegram", "1201")
    gts = [GeneratedTask(title="T1", due_date=TODAY + timedelta(days=1)),
           GeneratedTask(title="T2", due_date=TODAY + timedelta(days=2))]
    pid = projects.create_project(uid, "Meta", "", DEADLINE, gts)["id"]

    db = SessionLocal()
    db.query(TaskModel).filter(TaskModel.project_id == pid).first().completed = True
    db.commit()
    db.close()

    p = next(x for x in projects.list_projects(uid) if x["id"] == pid)
    assert p["done"] == 1 and p["total"] == 2

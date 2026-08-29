"""Task 14: reparto de tareas de un proyecto de equipo entre los miembros."""
import asyncio
from datetime import date, timedelta

from src.flowtask import main, projects, teams
from src.flowtask.infrastructure.ai_engine import GeneratedTask
from src.flowtask.infrastructure.database import (
    SessionLocal,
    TaskModel,
    get_or_create_user,
)

DEADLINE = date.today() + timedelta(days=30)


def _gts(n):
    return [
        GeneratedTask(title=f"T{i}", due_date=date.today() + timedelta(days=i + 1))
        for i in range(n)
    ]


def _team_of(n_members):
    owner = get_or_create_user("telegram", "9000")
    t = teams.create_team(owner, "Equipo")
    members = [owner]
    for i in range(1, n_members):
        u = get_or_create_user("telegram", f"900{i}")
        teams.join_team(u, t["invite_code"])
        members.append(u)
    return t, members


def test_balanced_assign_reparte_parejo():
    db = SessionLocal()
    res = projects._balanced_assign(db, [1, 2, 3], _gts(9))
    db.close()
    assert sorted(len(v) for v in res.values()) == [3, 3, 3]


def test_balanced_assign_respeta_carga_previa():
    _t, members = _team_of(3)
    a, b, c = members
    # a ya tiene 5 tareas pendientes asignadas
    db = SessionLocal()
    for i in range(5):
        db.add(TaskModel(user_id=a, assignee_id=a, title=f"prev{i}", category="TASK"))
    db.commit()
    res = projects._balanced_assign(db, members, _gts(3))
    db.close()
    assert len(res[a]) == 0 and len(res[b]) + len(res[c]) == 3


def test_create_project_de_equipo_asigna_todas():
    t, members = _team_of(3)
    owner = members[0]
    res = projects.create_project(owner, "Meta", "", DEADLINE, _gts(6), team_id=t["id"])

    db = SessionLocal()
    rows = db.query(TaskModel).filter(TaskModel.project_id == res["id"]).all()
    db.close()
    assert len(rows) == 6
    assert all(r.assignee_id in members and r.team_id == t["id"] for r in rows)
    assert sum(len(v) for v in res["assignments"].values()) == 6


def test_proyecto_personal_no_asigna():
    uid = get_or_create_user("telegram", "9500")
    res = projects.create_project(uid, "Solo", "", DEADLINE, _gts(3))
    assert res["assignments"] == {}
    db = SessionLocal()
    rows = db.query(TaskModel).filter(TaskModel.project_id == res["id"]).all()
    db.close()
    assert all(r.assignee_id is None for r in rows)


def test_list_projects_desglose_por_persona():
    t, members = _team_of(2)
    owner = members[0]
    pid = projects.create_project(owner, "MetaEq", "", DEADLINE, _gts(4), team_id=t["id"])["id"]
    p = next(x for x in projects.list_projects(owner) if x["id"] == pid)
    assert p["total"] == 4
    assert p["by_person"] and sum(
        int(f.split("/")[1]) for f in p["by_person"].values()
    ) == 4


def test_flujo_chat_equipo_notifica(monkeypatch):
    t, members = _team_of(2)
    owner = members[0]

    async def fake_plan(goal, rubric, deadline):
        return _gts(4)

    sent = []

    async def fake_send(platform, chat_id, text):
        sent.append((str(chat_id), text))
        return True

    monkeypatch.setattr(main.ai_engine, "decompose_goal", fake_plan)
    monkeypatch.setattr(main, "send_message", fake_send)

    def send(txt):
        return asyncio.run(main.handle_incoming_message("telegram", "9000", txt))

    send("/proyecto")
    send("Trabajo grupal")
    send("rúbrica X")
    send(DEADLINE.isoformat())
    send("Equipo")            # step "team"
    send("aceptar")

    # ambos miembros recibieron su parte
    assert {c for c, _ in sent} == {"9000", "9001"}
    assert all("Tu parte" in txt for _, txt in sent)

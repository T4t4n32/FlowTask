"""Task 5: equipos — crear, unirse por código, aislamiento y notificación."""
import asyncio

from src.flowtask import main, teams
from src.flowtask.infrastructure.database import (
    SessionLocal,
    TaskModel,
    get_or_create_user,
    new_session,
)


def test_crear_equipo_pone_al_dueno_como_miembro():
    ana = get_or_create_user("telegram", "10")
    t = teams.create_team(ana, "Proyecto Historia")
    assert len(t["invite_code"]) == 6
    mios = teams.list_teams(ana)
    assert any(x["name"] == "Proyecto Historia" and x["role"] == "owner" for x in mios)


def test_unirse_con_codigo_valido_es_idempotente():
    ana = get_or_create_user("telegram", "20")
    beto = get_or_create_user("telegram", "21")
    t = teams.create_team(ana, "Equipo Beta")

    r1 = teams.join_team(beto, t["invite_code"])
    r2 = teams.join_team(beto, t["invite_code"])
    assert r1 == r2 == {"id": t["id"], "name": "Equipo Beta"}
    assert any(x["role"] == "member" for x in teams.list_teams(beto))


def test_codigo_invalido_devuelve_none():
    ceci = get_or_create_user("telegram", "30")
    assert teams.join_team(ceci, "zzzzzz") is None


def test_no_miembro_no_encuentra_el_equipo_por_nombre():
    ana = get_or_create_user("telegram", "40")
    dani = get_or_create_user("telegram", "41")
    teams.create_team(ana, "Privado A")
    assert teams.get_member_team_by_name(dani, "Privado A") is None
    assert teams.get_member_team_by_name(ana, "privado a") is not None  # case-insensitive


def test_miembro_asignado_puede_completar_tarea_de_equipo():
    ana = get_or_create_user("telegram", "50")
    beto = get_or_create_user("telegram", "51")
    t = teams.create_team(ana, "Equipo Tareas")
    teams.join_team(beto, t["invite_code"])

    db = SessionLocal()
    task = TaskModel(user_id=ana, team_id=t["id"], assignee_id=beto,
                     title="Diapositivas", category="TASK")
    db.add(task)
    db.commit()
    tid = task.id
    db.close()

    res = asyncio.run(main.action_complete(tid, ft_token=new_session(beto)))
    assert res == {"ok": True}

    db = SessionLocal()
    assert db.get(TaskModel, tid).completed is True
    db.close()

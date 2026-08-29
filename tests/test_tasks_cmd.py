"""V1: gestión de tareas y hábitos desde el chat (/hecho, /borrar, /posponer, /habito, /ayuda)."""
import asyncio
from datetime import datetime, time, timedelta

from src.flowtask import habits, main
from src.flowtask.infrastructure.database import (
    SessionLocal,
    TaskModel,
    get_or_create_user,
)


def _send(text, chat_id="1"):
    return asyncio.run(main.handle_incoming_message("telegram", chat_id, text))


def _add_task(user_id, title="Tarea", due_at=None, completed=False):
    db = SessionLocal()
    t = TaskModel(user_id=user_id, title=title, category="TASK", due_at=due_at, completed=completed)
    db.add(t)
    db.commit()
    tid = t.id
    db.close()
    return tid


def _get(tid):
    db = SessionLocal()
    t = db.get(TaskModel, tid)
    row = (t.title, t.completed, t.due_at, t.reminder_sent) if t else None
    db.close()
    return row


def test_ayuda_y_start_devuelven_el_menu():
    assert "/hecho" in _send("/ayuda")
    assert "/hecho" in _send("/start")


def test_list_muestra_el_numero():
    uid = get_or_create_user("telegram", "1")
    tid = _add_task(uid, "Pagar luz")
    out = _send("/list")
    assert f"#{tid}" in out and "Pagar luz" in out


def test_hecho_completa_la_tarea():
    uid = get_or_create_user("telegram", "1")
    tid = _add_task(uid, "Comprar pan")
    r = _send(f"/hecho {tid}")
    assert "Hecho" in r and "Comprar pan" in r
    assert _get(tid)[1] is True


def test_hecho_de_otro_usuario_no_funciona():
    ana = get_or_create_user("telegram", "1")
    get_or_create_user("telegram", "2")
    tid = _add_task(ana, "Privada de Ana")
    r = asyncio.run(main.handle_incoming_message("telegram", "2", f"/hecho {tid}"))
    assert "No encuentro" in r
    assert _get(tid)[1] is False


def test_borrar_elimina():
    uid = get_or_create_user("telegram", "1")
    tid = _add_task(uid, "Basura")
    assert "Borrada" in _send(f"/borrar {tid}")
    assert _get(tid) is None


def test_posponer_cambia_fecha_y_reactiva_recordatorio():
    uid = get_or_create_user("telegram", "1")
    tid = _add_task(uid, "Llamar", due_at=datetime.now() - timedelta(hours=1))
    db = SessionLocal()
    db.get(TaskModel, tid).reminder_sent = True
    db.commit()
    db.close()

    r = _send(f"/posponer {tid} mañana a las 10")
    assert "movida" in r
    title, completed, due_at, reminder_sent = _get(tid)
    assert due_at > datetime.now() and reminder_sent is False


def test_posponer_sin_cuando_pide_aclaracion():
    uid = get_or_create_user("telegram", "1")
    tid = _add_task(uid)
    assert "cuándo" in _send(f"/posponer {tid} asdfgh").lower()


def test_habitos_lista_y_pausa():
    uid = get_or_create_user("telegram", "1")
    h = habits.create_habit(uid, "Meditar", time(7, 0))
    out = _send("/habitos")
    assert f"#{h['id']}" in out and "Meditar" in out and "07:00" in out

    assert "Pausado" in _send(f"/habito {h['id']} off")
    assert habits.rollover_habits() == 0  # inactivo -> no regenera

    assert "Activado" in _send(f"/habito {h['id']} on")


def test_habito_borrar():
    uid = get_or_create_user("telegram", "1")
    h = habits.create_habit(uid, "Correr", time(6, 0))
    assert "borrado" in _send(f"/habito {h['id']} borrar").lower()
    assert habits.list_habits(uid) == []

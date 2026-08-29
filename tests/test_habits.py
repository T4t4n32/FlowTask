"""Task 9: hábitos recurrentes — alta, instancia diaria idempotente, hora en /list."""
from datetime import date, datetime, time

from src.flowtask import habits, main
from src.flowtask.infrastructure.database import (
    HabitModel,
    SessionLocal,
    TaskModel,
    get_or_create_user,
)


def _tasks_for_habit(habit_id):
    db = SessionLocal()
    rows = db.query(TaskModel).filter(TaskModel.habit_id == habit_id).all()
    out = [(t.title, t.due_at, t.is_habit, t.category) for t in rows]
    db.close()
    return out


def test_crear_habito_genera_definicion_y_tarea_de_hoy():
    uid = get_or_create_user("telegram", "900")
    h = habits.create_habit(uid, "Leer 15 min", time(17, 0))

    db = SessionLocal()
    assert db.query(HabitModel).filter_by(id=h["id"]).first().active is True
    db.close()

    inst = _tasks_for_habit(h["id"])
    assert len(inst) == 1
    title, due_at, is_habit, cat = inst[0]
    assert title == "Leer 15 min"
    assert due_at == datetime.combine(date.today(), time(17, 0))
    assert is_habit is True and cat == "HABIT"


def test_rollover_no_duplica_si_ya_existe_hoy():
    uid = get_or_create_user("telegram", "901")
    h = habits.create_habit(uid, "Meditar", time(7, 0))
    assert habits.rollover_habits() == 0                 # hoy ya está
    assert len(_tasks_for_habit(h["id"])) == 1


def test_rollover_crea_la_instancia_del_dia():
    uid = get_or_create_user("telegram", "902")
    h = habits.create_habit(uid, "Gym", time(15, 0))

    # simular un día nuevo: borrar la instancia de hoy
    db = SessionLocal()
    db.query(TaskModel).filter(TaskModel.habit_id == h["id"]).delete()
    db.commit()
    db.close()

    assert habits.rollover_habits() == 1
    assert len(_tasks_for_habit(h["id"])) == 1


def test_habito_inactivo_no_se_regenera():
    uid = get_or_create_user("telegram", "903")
    h = habits.create_habit(uid, "Escribir diario", None)

    db = SessionLocal()
    db.query(TaskModel).filter(TaskModel.habit_id == h["id"]).delete()
    hb = db.query(HabitModel).filter_by(id=h["id"]).first()
    hb.active = False
    db.commit()
    db.close()

    assert habits.rollover_habits() == 0
    assert _tasks_for_habit(h["id"]) == []


def test_list_muestra_la_hora_del_habito():
    uid = get_or_create_user("telegram", "904")
    habits.create_habit(uid, "Estirar", time(8, 30))
    resumen = main.get_pending_tasks_summary(uid)
    assert "08:30 Estirar" in resumen

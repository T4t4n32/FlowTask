"""Task 4: cada usuario ve solo sus tareas."""
import os
import pathlib

# BD de test aislada, fijada ANTES de importar la app (config.load_dotenv no la pisa).
_DB = pathlib.Path(__file__).parent / "test_isolation.db"
_DB.unlink(missing_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{_DB.as_posix()}"

from src.flowtask import main  # noqa: E402  -> init_db() aplica las migraciones
from src.flowtask.infrastructure.database import (  # noqa: E402
    SessionLocal,
    TaskModel,
    get_or_create_user,
)


def _add_task(user_id: int, title: str, category: str = "TASK") -> None:
    db = SessionLocal()
    db.add(TaskModel(user_id=user_id, title=title, category=category, is_habit=False))
    db.commit()
    db.close()


def test_get_or_create_user_es_idempotente():
    a = get_or_create_user("telegram", 555)
    b = get_or_create_user("telegram", 555)
    assert a == b


def test_mismo_chat_id_distinta_plataforma_son_usuarios_distintos():
    assert get_or_create_user("telegram", 777) != get_or_create_user("whatsapp", 777)


def test_el_resumen_solo_trae_tareas_del_usuario():
    ana = get_or_create_user("telegram", 111)
    beto = get_or_create_user("telegram", 222)
    _add_task(ana, "Tarea de Ana")
    _add_task(beto, "Tarea de Beto")

    resumen_ana = main.get_pending_tasks_summary(ana)
    assert "Tarea de Ana" in resumen_ana
    assert "Tarea de Beto" not in resumen_ana


def test_no_se_completa_la_tarea_de_otro():
    import asyncio

    ana = get_or_create_user("telegram", 333)
    beto = get_or_create_user("telegram", 444)
    _add_task(ana, "Privada de Ana")

    db = SessionLocal()
    tid = db.query(TaskModel).filter(TaskModel.user_id == ana).first().id
    db.close()

    # Beto intenta completar la tarea de Ana -> no debe pasar nada.
    res = asyncio.run(main.action_complete(tid, beto))
    assert res == {"ok": False}

    db = SessionLocal()
    assert db.query(TaskModel).filter(TaskModel.id == tid).first().completed is False
    db.close()

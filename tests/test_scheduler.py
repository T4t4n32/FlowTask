"""Task 8: reminder_sweep manda avisos de tareas vencidas y marca reminder_sent."""
import asyncio
import os
import pathlib
from datetime import datetime, timedelta

_DB = pathlib.Path(__file__).parent / "test_scheduler.db"
_DB.unlink(missing_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{_DB.as_posix()}"

from src.flowtask import main, scheduler  # noqa: E402  -> init_db()
from src.flowtask.infrastructure.database import (  # noqa: E402
    SessionLocal,
    TaskModel,
    get_or_create_user,
)


def _make_task(user_id, due_at, completed=False, reminder_sent=False, title="Tarea X"):
    db = SessionLocal()
    t = TaskModel(
        user_id=user_id, title=title, category="TASK",
        due_at=due_at, completed=completed, reminder_sent=reminder_sent,
    )
    db.add(t)
    db.commit()
    tid = t.id
    db.close()
    return tid


class _FakeSender:
    def __init__(self, ok=True):
        self.ok = ok
        self.calls = []

    async def __call__(self, platform, chat_id, text):
        self.calls.append((platform, str(chat_id), text))
        return self.ok


def _run_sweep(monkeypatch, sender):
    monkeypatch.setattr(scheduler, "send_message", sender)
    asyncio.run(scheduler.reminder_sweep())


def _reminder_sent(tid):
    db = SessionLocal()
    v = db.get(TaskModel, tid).reminder_sent
    db.close()
    return v


def test_tarea_vencida_dispara_recordatorio(monkeypatch):
    uid = get_or_create_user("telegram", "800")
    tid = _make_task(uid, datetime.now() - timedelta(minutes=5), title="Pagar luz")
    sender = _FakeSender(ok=True)

    _run_sweep(monkeypatch, sender)

    assert len(sender.calls) == 1
    plat, chat, text = sender.calls[0]
    assert plat == "telegram" and chat == "800" and "Pagar luz" in text
    assert _reminder_sent(tid) is True


def test_no_se_repite_el_recordatorio(monkeypatch):
    uid = get_or_create_user("telegram", "801")
    _make_task(uid, datetime.now() - timedelta(hours=1))
    _run_sweep(monkeypatch, _FakeSender())          # 1ª pasada: marca reminder_sent
    sender2 = _FakeSender()
    _run_sweep(monkeypatch, sender2)                 # 2ª pasada: nada
    assert sender2.calls == []


def test_tarea_futura_no_dispara(monkeypatch):
    uid = get_or_create_user("telegram", "802")
    _make_task(uid, datetime.now() + timedelta(hours=2))
    sender = _FakeSender()
    _run_sweep(monkeypatch, sender)
    assert sender.calls == []


def test_tarea_completada_no_dispara(monkeypatch):
    uid = get_or_create_user("telegram", "803")
    _make_task(uid, datetime.now() - timedelta(hours=1), completed=True)
    sender = _FakeSender()
    _run_sweep(monkeypatch, sender)
    assert sender.calls == []


def test_si_falla_el_envio_no_marca_como_avisada(monkeypatch):
    uid = get_or_create_user("telegram", "804")
    tid = _make_task(uid, datetime.now() - timedelta(minutes=1))
    _run_sweep(monkeypatch, _FakeSender(ok=False))   # el envío falla
    assert _reminder_sent(tid) is False

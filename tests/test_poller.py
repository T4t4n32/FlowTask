"""Task 19 (adelantada): long-polling de Telegram para máquina propia."""
import asyncio

from src.flowtask import poller


def _run(coro):
    return asyncio.run(coro)


def test_dispatch_llama_handler_y_sender():
    calls = {}

    async def handler(platform, chat_id, text, name):
        calls["handler"] = (platform, str(chat_id), text, name)
        return "respuesta"

    async def sender(platform, chat_id, text):
        calls["sender"] = (platform, str(chat_id), text)

    upd = {
        "update_id": 5,
        "message": {"chat": {"id": 42}, "from": {"first_name": "Ana"}, "text": "hola"},
    }
    _run(poller._dispatch(upd, handler, sender))
    assert calls["handler"] == ("telegram", "42", "hola", "Ana")
    assert calls["sender"] == ("telegram", "42", "respuesta")


def test_dispatch_ignora_updates_sin_texto():
    called = []

    async def handler(*a):
        called.append(1)
        return ""

    async def sender(*a):
        called.append(1)

    _run(poller._dispatch({"update_id": 1, "message": {"chat": {"id": 1}}}, handler, sender))
    _run(poller._dispatch({"update_id": 2, "edited_message": {}}, handler, sender))
    assert called == []


def test_dispatch_no_envia_si_respuesta_vacia():
    sent = []

    async def handler(*a):
        return ""

    async def sender(*a):
        sent.append(1)

    _run(poller._dispatch(
        {"update_id": 1, "message": {"chat": {"id": 1}, "text": "x"}}, handler, sender
    ))
    assert sent == []


def test_dispatch_tolera_error_del_handler_y_avisa():
    sent = []

    async def handler(*a):
        raise RuntimeError("boom")

    async def sender(platform, chat_id, text):
        sent.append(text)

    # no debe propagar, y avisa al usuario
    _run(poller._dispatch(
        {"update_id": 1, "message": {"chat": {"id": 1}, "text": "x"}}, handler, sender
    ))
    assert sent and "Error interno" in sent[0]


def test_run_procesa_y_avanza_offset(monkeypatch):
    seen_offsets = []
    batches = [
        [{"update_id": 10, "message": {"chat": {"id": 1}, "text": "a"}}],
        [{"update_id": 11, "message": {"chat": {"id": 1}, "text": "b"}}],
    ]

    async def fake_get(client, offset):
        seen_offsets.append(offset)
        if batches:
            return batches.pop(0)
        raise asyncio.CancelledError

    async def fake_del(client):
        pass

    dispatched = []

    async def handler(p, c, t, n):
        dispatched.append(t)
        return ""

    async def sender(*a):
        pass

    monkeypatch.setattr(poller, "_get_updates", fake_get)
    monkeypatch.setattr(poller, "_delete_webhook", fake_del)
    try:
        _run(poller.run(handler, sender))
    except asyncio.CancelledError:
        pass

    assert dispatched == ["a", "b"]
    assert seen_offsets == [0, 11, 12]

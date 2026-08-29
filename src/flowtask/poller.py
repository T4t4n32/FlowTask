"""Long-polling de Telegram: pregunta por mensajes nuevos, sin URL pública.

Se usa cuando `TELEGRAM_POLLING=1` (máquina propia siempre encendida). El endpoint
`/webhook/telegram` sigue existiendo para el modo webhook, pero Telegram no permite
los dos a la vez → al arrancar se borra el webhook.
"""
import asyncio
import logging

import httpx

from .config import settings

logger = logging.getLogger(__name__)

_API = f"https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}"


async def _delete_webhook(client: httpx.AsyncClient) -> None:
    try:
        await client.post(f"{_API}/deleteWebhook", json={"drop_pending_updates": False})
    except Exception as e:  # noqa: BLE001
        logger.warning("deleteWebhook falló: %r", e)


async def _get_updates(client: httpx.AsyncClient, offset: int) -> list[dict]:
    r = await client.get(
        f"{_API}/getUpdates",
        params={"offset": offset, "timeout": 30, "allowed_updates": '["message"]'},
    )
    r.raise_for_status()
    return r.json().get("result", [])


async def run(handler, sender) -> None:
    """Bucle infinito. `handler(platform, chat_id, text, name) -> str`; `sender(platform, chat_id, text)`."""
    logger.info("Telegram polling arrancado")
    offset = 0
    async with httpx.AsyncClient(timeout=40.0) as client:
        await _delete_webhook(client)
        while True:
            try:
                updates = await _get_updates(client, offset)
            except asyncio.CancelledError:
                raise
            except Exception as e:  # noqa: BLE001
                logger.error("getUpdates falló: %r", e)
                await asyncio.sleep(3)
                continue
            for upd in updates:
                offset = upd["update_id"] + 1
                await _dispatch(upd, handler, sender)


async def _dispatch(upd: dict, handler, sender) -> None:
    msg = upd.get("message", {})
    if "text" not in msg:
        return
    chat_id = msg["chat"]["id"]
    name = msg.get("from", {}).get("first_name", "")
    try:
        reply = await handler("telegram", chat_id, msg["text"], name)
        if reply:
            await sender("telegram", chat_id, reply)
    except Exception as e:  # noqa: BLE001
        logger.error("poller._dispatch: %r", e)

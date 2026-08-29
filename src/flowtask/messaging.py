"""Envío de mensajes salientes. Un adaptador por plataforma (hoy solo Telegram)."""
import logging

import httpx

from .config import settings

logger = logging.getLogger(__name__)

_TELEGRAM_URL = f"https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/sendMessage"


async def send_message(platform: str, chat_id, text: str) -> bool:
    """Devuelve True si el mensaje se entregó."""
    if platform != "telegram":
        logger.warning("Plataforma no soportada aún: %s", platform)
        return False
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(
                _TELEGRAM_URL,
                json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
                timeout=5.0,
            )
            return r.status_code == 200
        except Exception as e:
            logger.error("Error enviando a %s: %s", platform, e)
            return False

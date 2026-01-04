import httpx

from ..core.config import settings
from ..core.logger import logger


class TelegramClient:
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    async def send_message(self, chat_id: int, text: str):
        url = f"{self.base_url}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Error en TelegramClient: {e}")
                return None

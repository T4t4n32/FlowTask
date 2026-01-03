"""
Cliente para Telegram Bot API.
"""
import logging
from typing import Dict, Any

import requests

from ..core.config import TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

class TelegramClient:
    """Cliente simple para Telegram Bot API."""
    
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN no configurado")
        
        self.base_url = f"https://api.telegram.org/bot{self.token}"
    
    def get_me(self) -> Dict[str, Any]:
        """Obtiene información del bot."""
        try:
            response = requests.get(f"{self.base_url}/getMe", timeout=10)
            data = response.json()
            
            if data.get("ok"):
                return data["result"]
            else:
                logger.error(f"Error Telegram API: {data.get('description')}")
                return {}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión: {e}")
            return {}
    
    def send_message(self, chat_id: int, text: str) -> bool:
        """Envía un mensaje a un chat."""
        try:
            response = requests.post(
                f"{self.base_url}/sendMessage",
                json={"chat_id": chat_id, "text": text},
                timeout=10
            )
            return response.json().get("ok", False)
        except Exception as e:
            logger.error(f"Error enviando mensaje: {e}")
            return False

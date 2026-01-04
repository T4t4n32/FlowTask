import os
import json
import httpx
import logging
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class AIResponse(BaseModel):
    intent: str = "SAVE"
    category: str = "TASK"
    clean_title: str = ""
    is_habit: bool = False
    ids_to_complete: List[int] = []

class AIEngine:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={self.api_key}"

    def _manual_logic(self, text: str) -> AIResponse:
        t = text.lower()
        if any(w in t for w in ["pagar", "factura", "banco", "urgente", "cita", "reunion", "importante", "jefe", "entrega", "examen"]):
            return AIResponse(category="MANGO_REL", clean_title=text[:25].capitalize(), is_habit=False)
        if any(w in t for w in ["cada", "diario", "gym", "meditar", "leer", "rutina", "siempre", "entrenar"]):
            return AIResponse(category="HABIT", clean_title=text[:25].capitalize(), is_habit=True)
        return AIResponse(category="TASK", clean_title=text[:25].capitalize(), is_habit=False)

    async def classify_text(self, text: str) -> AIResponse:
        if not self.api_key: return self._manual_logic(text)
        payload = {"contents": [{"parts": [{"text": f"Clasifica en JSON (category, clean_title, is_habit). Mensaje: {text}"}]}]}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.url, json=payload, timeout=5.0)
                if response.status_code != 200: return self._manual_logic(text)
                data = response.json()
                if 'candidates' in data:
                    content = data['candidates'][0]['content']['parts'][0]['text']
                    res = json.loads(content.strip().replace("```json", "").replace("```", ""))
                    t = text.lower()
                    if any(w in t for w in ["pagar", "urgente", "cita"]):
                        res["category"] = "MANGO_REL"
                        res["is_habit"] = False
                    res["is_habit"] = True if res["category"] == "HABIT" else False
                    return AIResponse(**res)
                return self._manual_logic(text)
        except Exception:
            return self._manual_logic(text)
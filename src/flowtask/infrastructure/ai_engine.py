import os
import json
import httpx
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv

load_dotenv()

class AIResponse(BaseModel):
    intent: str = "SAVE"
    category: str = "TASK"
    clean_title: str = ""
    is_habit: bool = False
    ids_to_complete: List[int] = []

class AIEngine:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"

    async def classify_text(self, text: str) -> AIResponse:
        low_text = text.lower().strip()
        
        # --- ATAJOS DIRECTOS (PUERTA TRASERA) ---
        if low_text.startswith("habito:"):
            return AIResponse(intent="SAVE", category="HABIT", clean_title=text[7:].strip(), is_habit=True)
        if low_text.startswith("tarea:"):
            return AIResponse(intent="SAVE", category="TASK", clean_title=text[6:].strip(), is_habit=False)
        if low_text.startswith("mango:"):
            return AIResponse(intent="SAVE", category="MANGO_REL", clean_title=text[6:].strip(), is_habit=False)

        # --- LÓGICA DE IA ---
        prompt = (
            f"Analiza: '{text}'. Responde estrictamente un JSON: "
            "{\"intent\": \"SAVE\"/\"COMPLETE\", \"category\": \"HABIT\"/\"MANGO_REL\"/\"TASK\", "
            "\"clean_title\": \"texto\", \"is_habit\": bool, \"ids_to_complete\": []}"
        )
        
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(self.url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=10.0)
                raw_res = res.json()['candidates'][0]['content']['parts'][0]['text']
                data = json.loads(raw_res.strip().replace("```json", "").replace("```", ""))
                return AIResponse(**data)
        except Exception as e:
            print(f"Fallback IA por error: {e}")
            return AIResponse(intent="SAVE", category="TASK", clean_title=text, is_habit=False)
import json
import logging
from datetime import date, datetime, time, timedelta
from typing import List

import httpx
from pydantic import BaseModel

from ..config import settings

logger = logging.getLogger(__name__)

class AIResponse(BaseModel):
    intent: str = "SAVE"  # Opciones: SAVE, CHAT, COMMAND
    category: str = "TASK"
    clean_title: str = ""
    response_text: str = "" # Para que la IA pueda responderte si es charla
    is_habit: bool = False
    ids_to_complete: List[int] = []


class GeneratedTask(BaseModel):
    title: str
    due_date: date
    note: str = ""

class AIEngine:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.GEMINI_MODEL}:generateContent?key={self.api_key}"
        )

    def _manual_override(self, text: str, data: dict) -> dict:
        """
        Capa final de decisión. Corrige a la IA y detecta saludos simples.
        """
        t = text.lower().strip()
        
        # 1. Detectar Conversación/Saludos simples (Para evitar crear tareas basura)
        chat_triggers = ["hola", "hi", "buenos dias", "buenas", "que tal", "test", "probando"]
        if t in chat_triggers or len(t) < 3:
            data["intent"] = "CHAT"
            data["response_text"] = "👋 ¡Hola! FlowTask listo. Dime una tarea, hábito o mango."
            return data

        # 2. Palabras Clave de MANGO (Prioridad Máxima)
        mango_triggers = ["pagar", "factura", "banco", "cita", "reunion", "urgente", "jefe", "médico", "examen", "entrega", "deuda", "impuesto", "vencimiento"]
        
        # 3. Palabras Clave de HABIT (Rutinas)
        habit_triggers = ["cada", "diario", "siempre", "rutina", "gym", "meditar", "leer", "entrenar", "estudiar", "vitaminas", "agua"]

        if any(w in t for w in mango_triggers):
            data["category"] = "MANGO_REL"
            data["is_habit"] = False
            data["intent"] = "SAVE"
        elif any(w in t for w in habit_triggers):
            data["category"] = "HABIT"
            data["is_habit"] = True
            data["intent"] = "SAVE"
            
        return data

    async def classify_text(self, text: str) -> AIResponse:
        system_context = (
            "Clasifica el mensaje. Responde SOLO con JSON, sin markdown.\n"
            'Campos: intent ("SAVE"|"CHAT"), category ("MANGO_REL"|"HABIT"|"TASK"), '
            "clean_title (str corto, SIN fechas ni horas), "
            "response_text (str, solo si intent=CHAT), is_habit (bool).\n"
            "MANGO_REL=dinero/pagos/citas médicas/reuniones/urgencias. "
            "HABIT=rutinas repetidas (gym, salud, lectura). TASK=compras/recados/ideas. "
            "CHAT=saludo o charla sin acción."
        )

        default_data = {
            "intent": "SAVE",
            "category": "TASK",
            "clean_title": text[:30],
            "is_habit": False,
            "response_text": ""
        }

        payload = {
            "contents": [{"parts": [{"text": f"{system_context}\n\nMENSAJE: {text}"}]}]
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.url, json=payload, timeout=15.0)
                
                if response.status_code == 200:
                    res_json = response.json()
                    if 'candidates' in res_json:
                        raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
                        clean_json = raw_text.strip().replace("```json", "").replace("```", "")
                        data = json.loads(clean_json)
                    else:
                        data = default_data
                else:
                    logger.warning(f"API Error {response.status_code}, usando fallback.")
                    data = default_data

                # APLICAR REGLAS MANUALES AL FINAL (Tus reglas se respetan aquí)
                final_data = self._manual_override(text, data)

                # Sincronización de seguridad
                if final_data.get("category") == "HABIT":
                    final_data["is_habit"] = True

                # El modelo a veces devuelve campos en null; quitarlos deja que apliquen los defaults.
                final_data = {k: v for k, v in final_data.items() if v is not None}
                return AIResponse(**final_data)

        except Exception as e:
            logger.error(f"Excepción crítica en AI: {e!r}")
            # En caso de error total, usamos el manual override sobre los datos por defecto
            fallback_data = self._manual_override(text, default_data)
            return AIResponse(**fallback_data)

    async def _call_gemini(self, prompt: str) -> dict:
        """Llama a Gemini y devuelve el JSON. Lanza excepción si falla."""
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        async with httpx.AsyncClient() as client:
            r = await client.post(self.url, json=payload, timeout=20.0)
        r.raise_for_status()
        raw = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(raw.strip().replace("```json", "").replace("```", ""))

    async def decompose_goal(
        self, goal: str, rubric: str, deadline: date
    ) -> list[GeneratedTask]:
        """Descompone una meta en tareas diarias con fecha. Fallback: hitos semanales."""
        today = date.today()
        prompt = (
            f"Eres un planificador. Hoy es {today.isoformat()}. "
            f'Meta: "{goal}". Fecha límite: {deadline.isoformat()}. '
            f"Rúbrica de evaluación: {rubric or '(no especificada)'}.\n"
            "Divide la meta en 4-8 tareas concretas y accionables, repartidas entre hoy y la "
            "fecha límite (NO todas al final). Cada tarea debe apuntar a un resultado por encima "
            "del promedio y cubrir la rúbrica.\n"
            'Responde SOLO con JSON: {"tasks": [{"title": "...", "due_date": "YYYY-MM-DD", '
            '"note": "qué entregar / por qué"}]}'
        )
        try:
            data = await self._call_gemini(prompt)
            out: list[GeneratedTask] = []
            for item in data.get("tasks", []):
                gt = GeneratedTask(**item)
                gt.due_date = min(max(gt.due_date, today), deadline)  # dentro del rango
                out.append(gt)
            if len(out) >= 3:
                out.sort(key=lambda t: t.due_date)
                return out
            logger.warning("decompose_goal: la IA devolvió %d tareas, usando fallback", len(out))
        except Exception as e:
            logger.error("decompose_goal falló (%r), usando fallback", e)
        return self._fallback_plan(goal, deadline, today)

    @staticmethod
    def _fallback_plan(goal: str, deadline: date, today: date) -> list[GeneratedTask]:
        span = max((deadline - today).days, 1)
        n = max(2, min(6, span // 7 + 1))
        step = span / n
        return [
            GeneratedTask(
                title=f"{goal} — hito {i + 1}/{n}",
                due_date=today + timedelta(days=round(step * (i + 1))),
                note="Plan automático (IA no disponible)",
            )
            for i in range(n)
        ]
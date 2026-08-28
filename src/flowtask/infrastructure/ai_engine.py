import json
import httpx
import logging
from pydantic import BaseModel
from typing import List

from ..config import settings

logger = logging.getLogger(__name__)

class AIResponse(BaseModel):
    intent: str = "SAVE"  # Opciones: SAVE, CHAT, COMMAND
    category: str = "TASK"
    clean_title: str = ""
    response_text: str = "" # Para que la IA pueda responderte si es charla
    is_habit: bool = False
    ids_to_complete: List[int] = []

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
        # Prompt más robusto para conversación y diferenciación
        system_context = """
        ERES FLOWTASK AI. TU OBJETIVO ES CLASIFICAR O CONVERSAR.
        
        SI ES UNA ACCIÓN A GUARDAR (Intent: SAVE):
        1. MANGO_REL: Dinero, Pagos, Citas Médicas, Reuniones, Urgencias.
        2. HABIT: Acciones repetitivas, Gym, Salud, Lectura.
        3. TASK: Compras simples, recados, ideas.
        
        SI ES SOLO CHARLA (Intent: CHAT):
        - Responde amablemente en 'response_text'.
        
        FORMATO JSON REQUERIDO:
        {
            "intent": "SAVE" | "CHAT",
            "category": "MANGO_REL" | "HABIT" | "TASK",
            "clean_title": "Título corto",
            "response_text": "Texto de respuesta si es chat",
            "is_habit": boolean
        }
        """
        
        default_data = {
            "intent": "SAVE", 
            "category": "TASK", 
            "clean_title": text[:30], 
            "is_habit": False, 
            "response_text": ""
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.url,
                    json={"contents": [{"parts": [{"text": f"{system_context}\n\nINPUT USUARIO: {text}"}]}]},
                    timeout=8.0
                )
                
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
                
                return AIResponse(**final_data)

        except Exception as e:
            logger.error(f"Excepción crítica en AI: {e}")
            # En caso de error total, usamos el manual override sobre los datos por defecto
            fallback_data = self._manual_override(text, default_data)
            return AIResponse(**fallback_data)
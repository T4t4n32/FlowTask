import os
import json
import httpx
from pydantic import BaseModel
from typing import List, Optional
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
        # PROMPT DE ALTA INTENSIDAD PARA DIFERENCIACIÓN TOTAL
        system_context = """
        ACTÚA COMO EL NÚCLEO DE FLOWTASK OS. TU MISIÓN ES TRANSFORMAR LENGUAJE NATURAL EN JSON.

        REGLAS DE CATEGORÍA:
        1. MANGO_REL: Compromisos críticos, PAGOS, REUNIONES, citas médicas, urgencias, trabajo con terceros.
           - Ejemplo: "Llamar al cliente", "Pagar recibo", "Cita dentista", "Reunión 3pm".
        2. HABIT: Rutinas, salud, ejercicio, estudio repetitivo, autocuidado.
           - Ejemplo: "Gym", "Meditar", "Leer 10 min", "Cada mañana".
        3. TASK: Recados simples, compras, cosas para el inbox sin urgencia.
           - Ejemplo: "Comprar pan", "Ver serie", "Limpiar mesa".

        RESPONDE ESTRICTAMENTE JSON:
        {
          "category": "MANGO_REL" | "HABIT" | "TASK",
          "clean_title": "Máximo 3 palabras",
          "is_habit": boolean
        }
        """

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.url, 
                    json={"contents": [{"parts": [{"text": f"{system_context}\n\nMENSAJE: {text}"}]}]}, 
                    timeout=12.0
                )
                res_data = response.json()
                
                # Extracción segura
                raw_output = res_data['candidates'][0]['content']['parts'][0]['text']
                clean_json = raw_output.strip().replace("```json", "").replace("```", "")
                data = json.loads(clean_json)

                # VALIDACIÓN MANUAL POST-IA (FORCE MANGO/HABIT)
                t = text.lower()
                mango_triggers = ["pagar", "factura", "banco", "reunion", "cita", "urgente", "jefe", "médico", "examen"]
                habit_triggers = ["cada", "diario", "siempre", "gym", "meditar", "rutina", "entrenar", "mañana"]

                if any(w in t for w in mango_triggers):
                    data["category"] = "MANGO_REL"
                    data["is_habit"] = False
                elif any(w in t for w in habit_triggers):
                    data["category"] = "HABIT"
                    data["is_habit"] = True

                # Sincronización de booleano
                data["is_habit"] = True if data["category"] == "HABIT" else False
                
                return AIResponse(**data)
        except Exception as e:
            print(f"DEBUG: Error AI Engine: {e}")
            # FALLBACK DE EMERGENCIA: No dejar al usuario sin respuesta
            return AIResponse(intent="SAVE", category="TASK", clean_title=text[:25], is_habit=False)
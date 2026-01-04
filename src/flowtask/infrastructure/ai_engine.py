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
        # Prompt de nivel industrial con lógica de discriminación
        instruction = f"""
        ACTÚA COMO UN SISTEMA OPERATIVO LÓGICO DE PRODUCTIVIDAD.
        Tu tarea es procesar el siguiente mensaje del usuario y clasificarlo en una de las 3 categorías del sistema.

        --- CRITERIOS DE EVALUACIÓN ---
        
        1. MANGO_REL (Prioridad Crítica):
           - Definición: Tareas únicas que NO son rutinarias pero son VITALES o URGENTES.
           - Palabras clave disparadoras: "urgente", "importante", "hoy mismo", "reunión", "entregar", "llamar a", "pagar", "proyecto", "examen".
           - Diferenciación: Si es algo que se hace una vez pero tiene consecuencias si no se hace, es MANGO.

        2. HABIT (Hábito/Rutina):
           - Definición: Acciones repetitivas que forman parte de un estilo de vida o disciplina.
           - Palabras clave disparadoras: "siempre", "cada día", "todas las mañanas", "diario", "rutina", "entrenar", "meditar", "leer", "estudiar", "limpiar", "gym".
           - REGLA DE ORO: Si la acción es recurrente, SIEMPRE es HABIT, sin importar qué tan importante sea.

        3. TASK (Tarea General):
           - Definición: Recados de baja prioridad, cosas para el "Inbox" que no son urgentes ni recurrentes.
           - Palabras clave disparadoras: "comprar", "traer", "ver", "buscar", "recoger".
           - Diferenciación: Si no encaja en las anteriores, cae aquí por defecto.

        --- REGLAS DE FORMATEO ---
        - 'clean_title': Extrae el núcleo de la acción. Elimina "tengo que", "recuérdame", "quiero". Máximo 4 palabras.
        - 'is_habit': Debe ser TRUE solo si la categoría es HABIT.

        --- ANÁLISIS PASO A PASO ---
        Mensaje del usuario: "{text}"

        Responde ÚNICAMENTE en este formato JSON:
        {{
          "category": "MANGO_REL" | "HABIT" | "TASK",
          "clean_title": "String",
          "is_habit": boolean
        }}
        """

        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(self.url, json={"contents": [{"parts": [{"text": instruction}]}]}, timeout=20.0)
                raw_data = res.json()['candidates'][0]['content']['parts'][0]['text']
                # Limpieza de posibles tags de markdown que devuelve la IA
                clean_json = raw_data.strip().replace("```json", "").replace("```", "")
                parsed = json.loads(clean_json)
                
                # Post-procesamiento de seguridad para evitar errores de la IA
                if parsed['category'] == "HABIT":
                    parsed['is_habit'] = True
                else:
                    parsed['is_habit'] = False

                return AIResponse(**parsed)
        except Exception as e:
            print(f"ERROR CRÍTICO IA: {e}")
            # Fallback lógico manual si la IA falla
            return self._manual_fallback(text)

    def _manual_fallback(self, text: str) -> AIResponse:
        t = text.lower()
        if any(w in t for w in ["cada", "diario", "gym", "meditar", "leer"]):
            return AIResponse(category="HABIT", clean_title=text[:20], is_habit=True)
        if any(w in t for w in ["urgente", "importante", "pagar", "llamar"]):
            return AIResponse(category="MANGO_REL", clean_title=text[:20], is_habit=False)
        return AIResponse(category="TASK", clean_title=text[:20], is_habit=False)
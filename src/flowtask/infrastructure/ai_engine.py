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
        system_prompt = """
        Eres el 'FlowTask OS Core', un sistema de inteligencia avanzada para productividad. 
        Tu objetivo es convertir mensajes informales en datos estructurados.

        REGLAS DE CLASIFICACIÓN:
        1. MANGO_REL (Prioridad): Tareas críticas, proyectos importantes, urgencias o compromisos de alto valor.
           - Ejemplo: "Enviar propuesta al cliente", "Llamar al abogado", "Urgente arreglar la fuga".
        2. HABIT (Hábito): Acciones que se repiten, rutinas de salud, estudio o bienestar.
           - Ejemplo: "Ir al gym", "Meditar", "Leer 20 min", "Tomar agua".
        3. TASK (Tarea): Recados comunes, recordatorios simples de un solo paso.
           - Ejemplo: "Comprar pan", "Sacar la basura", "Lavar el carro".

        REGLAS DE TÍTULO (clean_title):
        - Resume la acción a máximo 4 palabras.
        - Elimina palabras innecesarias como "recuerdame", "tengo que", "porfa".
        - Usa mayúscula inicial.

        RESPONDE ESTRICTAMENTE EN JSON:
        {
          "intent": "SAVE",
          "category": "MANGO_REL" | "HABIT" | "TASK",
          "clean_title": "Título corto",
          "is_habit": true (solo si es HABIT) o false
        }

        EJEMPLOS:
        - "No me dejes olvidar pagar la luz hoy" -> {"category": "MANGO_REL", "clean_title": "Pagar factura luz", "is_habit": false}
        - "Quiero empezar a caminar cada mañana" -> {"category": "HABIT", "clean_title": "Caminar mañana", "is_habit": true}
        - "Hay que comprar tomates" -> {"category": "TASK", "clean_title": "Comprar tomates", "is_habit": false}
        """

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "contents": [{"parts": [{"text": f"{system_prompt}\n\nMensaje: {text}"}]}]
                }
                res = await client.post(self.url, json=payload, timeout=15.0)
                raw_res = res.json()['candidates'][0]['content']['parts'][0]['text']
                data = json.loads(raw_res.strip().replace("```json", "").replace("```", ""))
                
                # Doble verificación de seguridad
                if data['category'] == "HABIT":
                    data['is_habit'] = True
                else:
                    data['is_habit'] = False
                    
                return AIResponse(**data)
        except Exception as e:
            print(f"Error AI: {e}")
            return AIResponse(intent="SAVE", category="TASK", clean_title=text, is_habit=False)
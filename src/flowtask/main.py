import os
import httpx
import sys
from datetime import datetime, date
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

# Rutas para Railway
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../../"))
sys.path.append(PROJECT_ROOT)

from src.flowtask.infrastructure.ai_engine import AIEngine
from src.flowtask.infrastructure.database import init_db, SessionLocal, TaskModel, save_to_db

load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, ".env"))

app = FastAPI()
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Inicialización
init_db()
ai_engine = AIEngine()

# Telegram Config
TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"

async def reply_telegram(chat_id: int, text: str):
    async with httpx.AsyncClient() as client:
        await client.post(f"{TELEGRAM_API}/sendMessage", json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        })

@app.post("/webhook/telegram")
async def handle_telegram(request: Request):
    try:
        data = await request.json()
        if "message" not in data or "text" not in data["message"]:
            return {"status": "no_text"}

        chat_id = data["message"]["chat"]["id"]
        original_text = data["message"]["text"]

        # 1. Procesamiento IA de alta intensidad
        ai_res = await ai_engine.classify_text(original_text)
        
        # 2. Persistencia en base de datos
        save_to_db(ai_res)

        # 3. Respuesta visual clara en Telegram
        emoji_map = {
            "MANGO_REL": "🥭 *[MANGO]* Prioridad crítica guardada.",
            "HABIT": "🔄 *[HÁBITO]* Rutina diaria registrada.",
            "TASK": "✅ *[TAREA]* Añadida al inbox."
        }
        msg = f"{emoji_map.get(ai_res.category)}\n\n*Título:* {ai_res.clean_title}"
        
        await reply_telegram(chat_id, msg)
        
    except Exception as e:
        print(f"Error procesando Telegram: {e}")
    
    return {"status": "ok"}

# Mantengo el dashboard solo para visualización
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    db = SessionLocal()
    today = date.today()
    try:
        items = db.query(TaskModel).filter(TaskModel.created_at >= today).all()
        # Lógica de filtrado para el HTML...
        # (Aquí va el retorno de templates que ya tienes)
        return templates.TemplateResponse("dashboard.html", {
            "request": request, "user_name": "Tatan", "dia_num": datetime.now().day,
            "mes_txt": "ENERO", "fecha_friendly": "4 de Enero", "saludo": "Hola",
            "mango": [i for i in items if i.category == "MANGO_REL" and not i.completed],
            "habits": [i for i in items if i.is_habit and not i.completed],
            "tasks": [i for i in items if i.category == "TASK" and not i.is_habit and not i.completed],
            "stats": {"h_done": 0, "h_total": 0, "t_done": 0, "t_total": 0}
        })
    finally:
        db.close()

@app.post("/complete/{task_id}")
async def complete(task_id: int):
    db = SessionLocal()
    t = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if t: t.completed = True; db.commit()
    db.close()
    return {"ok": True}
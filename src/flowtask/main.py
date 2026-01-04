import os
import httpx
import sys
from datetime import datetime, date, timedelta
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

# Configuración de rutas para Railway
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../../"))
sys.path.append(PROJECT_ROOT)

from src.flowtask.infrastructure.ai_engine import AIEngine
from src.flowtask.infrastructure.database import init_db, SessionLocal, TaskModel, save_to_db

load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, ".env"))

app = FastAPI()
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

init_db()
ai_engine = AIEngine()

TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
TELEGRAM_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

async def send_telegram(chat_id: int, text: str):
    async with httpx.AsyncClient() as client:
        await client.post(TELEGRAM_URL, json={
            "chat_id": chat_id, 
            "text": text, 
            "parse_mode": "Markdown"
        })

@app.get("/dashboard", response_class=HTMLResponse)
async def view_dashboard(request: Request):
    db = SessionLocal()
    today = date.today()
    try:
        all_items = db.query(TaskModel).filter(TaskModel.created_at >= today).all()
        
        mango = [i for i in all_items if i.category == "MANGO_REL" and not i.completed]
        habits = [i for i in all_items if i.is_habit and not i.completed]
        tasks = [i for i in all_items if i.category == "TASK" and not i.is_habit and not i.completed]

        h_total = [i for i in all_items if i.is_habit]
        t_total = [i for i in all_items if i.category == "TASK" and not i.is_habit]

        ahora = datetime.now()
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "user_name": "Tatan",
            "dia_num": ahora.day,
            "mes_txt": meses[ahora.month-1].upper(),
            "fecha_friendly": f"{ahora.day} de {meses[ahora.month-1]}",
            "saludo": "Buenos días" if ahora.hour < 12 else "Buenas tardes" if ahora.hour < 18 else "Buenas noches",
            "mango": mango,
            "habits": habits,
            "tasks": tasks,
            "stats": {
                "h_done": len([i for i in h_total if i.completed]),
                "h_total": len(h_total),
                "t_done": len([i for i in t_total if i.completed]),
                "t_total": len(t_total)
            }
        })
    finally:
        db.close()

@app.post("/complete/{task_id}")
async def action_complete(task_id: int):
    db = SessionLocal()
    item = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if item:
        item.completed = True
        db.commit()
    db.close()
    return {"ok": True}

@app.get("/api/history/{category_type}")
async def get_history(category_type: str):
    db = SessionLocal()
    today = date.today()
    # Trae lo completado hoy para el historial
    items = db.query(TaskModel).filter(TaskModel.created_at >= today, TaskModel.completed == True).all()
    if category_type == "habits":
        filtered = [i for i in items if i.is_habit]
    else:
        filtered = [i for i in items if not i.is_habit]
    db.close()
    return [{"title": i.title, "time": i.created_at.strftime("%H:%M"), "status": "✅"} for i in filtered]

@app.post("/webhook/telegram")
async def telegram_endpoint(request: Request):
    data = await request.json()
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]
        ai_res = await ai_engine.classify_text(text)
        save_to_db(ai_res)
        
        icons = {"MANGO_REL": "🥭 *MANGO*", "HABIT": "🔄 *HÁBITO*", "TASK": "✅ *TAREA*"}
        ico = icons.get(ai_res.category, "📌")
        await send_telegram(chat_id, f"{ico}\n{ai_res.clean_title}")
    return {"ok": True}
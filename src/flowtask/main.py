import os
import httpx
import sys
import logging
from datetime import datetime, date
from typing import Optional
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from dotenv import load_dotenv

# Configuración de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
TELEGRAM_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

async def send_msg(chat_id: int, text: str):
    """Envía mensajes a Telegram."""
    async with httpx.AsyncClient() as client:
        try:
            await client.post(TELEGRAM_URL, json={
                "chat_id": chat_id, "text": text, "parse_mode": "Markdown"
            }, timeout=5.0)
        except Exception as e:
            logger.error(f"Error enviando a Telegram: {e}")

def get_pending_tasks_summary():
    """Genera un resumen de tareas pendientes para el comando /list."""
    db = SessionLocal()
    try:
        today = date.today()
        # Filtramos tareas de hoy que no estén completadas
        items = db.query(TaskModel).filter(
            func.date(TaskModel.created_at) == today, 
            TaskModel.completed == False
        ).all()
        
        if not items:
            return "👍 *Todo limpio.* No tienes tareas pendientes hoy."

        mango = [i.title for i in items if i.category == "MANGO_REL"]
        habits = [i.title for i in items if i.is_habit]
        tasks = [i.title for i in items if i.category == "TASK" and not i.is_habit]

        msg = f"📅 *Resumen del {today.strftime('%d/%m')}*\n\n"
        if mango: msg += "🥭 *PRIORIDAD MANGO*\n" + "\n".join([f"- {t}" for t in mango]) + "\n\n"
        if habits: msg += "🔄 *HÁBITOS*\n" + "\n".join([f"- {t}" for t in habits]) + "\n\n"
        if tasks: msg += "✅ *TAREAS*\n" + "\n".join([f"- {t}" for t in tasks])
        
        return msg
    finally:
        db.close()

@app.get("/dashboard", response_class=HTMLResponse)
async def view_dashboard(request: Request, date_param: Optional[str] = None):
    db = SessionLocal()
    try:
        # Lógica de fecha segura
        if date_param:
            try:
                target_date = datetime.strptime(date_param, "%Y-%m-%d").date()
            except:
                target_date = date.today()
        else:
            target_date = date.today()

        items = db.query(TaskModel).filter(func.date(TaskModel.created_at) == target_date).all()
        
        mango = [i for i in items if i.category == "MANGO_REL" and not i.completed]
        habits = [i for i in items if i.is_habit and not i.completed]
        tasks = [i for i in items if i.category == "TASK" and not i.is_habit and not i.completed]

        # Cálculos para estadísticas
        h_all = [i for i in items if i.is_habit]
        t_all = [i for i in items if not i.is_habit]

        stats = {
            "h_done": int(len([i for i in h_all if i.completed])),
            "h_total": int(len(h_all)),
            "t_done": int(len([i for i in t_all if i.completed])),
            "t_total": int(len(t_all))
        }

        meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]

        return templates.TemplateResponse(request, "dashboard.html", {
            "dia_num": target_date.day,
            "mes_txt": meses[target_date.month-1],
            "current_date_iso": target_date.isoformat(),
            "mango": mango,
            "habits": habits,
            "tasks": tasks,
            "stats": stats
        })
    finally:
        db.close()

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        if "message" not in data or "text" not in data["message"]:
            return {"ok": True}

        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"].strip()

        # --- 1. INTERCEPTOR DE COMANDOS (Nuevo) ---
        if text.startswith("/list"):
            summary = get_pending_tasks_summary()
            background_tasks.add_task(send_msg, chat_id, summary)
            return {"ok": True}

        # --- 2. PROCESAMIENTO DE IA ---
        ai_res = await ai_engine.classify_text(text)

        # Si es solo charla, respondemos y NO guardamos
        if ai_res.intent == "CHAT":
            response_txt = ai_res.response_text if ai_res.response_text else "🤖 Escuchando..."
            background_tasks.add_task(send_msg, chat_id, response_txt)
            return {"ok": True}

        # Si es una tarea válida (SAVE), guardamos
        save_to_db(ai_res)

        icons = {"MANGO_REL": "🥭 *MANGO*", "HABIT": "🔄 *HÁBITO*", "TASK": "✅ *TAREA*"}
        msg = f"{icons.get(ai_res.category, '📌')}\n\n*Registrado:* {ai_res.clean_title}"
        
        background_tasks.add_task(send_msg, chat_id, msg)

    except Exception as e:
        logger.error(f"Falla Webhook: {e}")
    
    return {"ok": True}

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
    items = db.query(TaskModel).filter(TaskModel.created_at >= today, TaskModel.completed == True).all()
    if category_type == "habits":
        filtered = [i for i in items if i.is_habit]
    else:
        filtered = [i for i in items if not i.is_habit]
    db.close()
    return [{"title": i.title, "time": i.created_at.strftime("%H:%M")} for i in filtered]
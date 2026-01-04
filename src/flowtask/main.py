import os
import httpx
import sys
import logging
from datetime import datetime, date
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

# Configuración de logs para ver errores en Railway
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

init_db()
ai_engine = AIEngine()

# TOKEN DE TELEGRAM
TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
TELEGRAM_SEND_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

async def notify_telegram(chat_id: int, text: str):
    """Función aislada para enviar mensajes y evitar que el webhook cuelgue."""
    async with httpx.AsyncClient() as client:
        try:
            await client.post(TELEGRAM_SEND_URL, json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }, timeout=5.0)
        except Exception as e:
            logger.error(f"Error enviando a Telegram: {e}")

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        if "message" not in data or "text" not in data["message"]:
            return {"ok": True}

        chat_id = data["message"]["chat"]["id"]
        original_text = data["message"]["text"]

        # 1. Procesar con IA
        ai_res = await ai_engine.classify_text(original_text)
        
        # 2. Guardar en DB
        save_to_db(ai_res)

        # 3. Preparar respuesta estética
        icons = {"MANGO_REL": "🥭 *MANGO*", "HABIT": "🔄 *HÁBITO*", "TASK": "✅ *TAREA*"}
        response_msg = f"{icons.get(ai_res.category, '📌')}\n\n*Registrado:* {ai_res.clean_title}"
        
        # 4. Enviar notificación (Background para no bloquear el webhook)
        background_tasks.add_task(notify_telegram, chat_id, response_msg)

    except Exception as e:
        logger.error(f"Falla crítica en Webhook: {e}")
        
    return {"ok": True}

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_view(request: Request):
    db = SessionLocal()
    today = date.today()
    try:
        # Obtener todos los ítems de hoy
        all_items = db.query(TaskModel).filter(TaskModel.created_at >= today).all()
        
        # Listas para renderizado
        mango = [i for i in all_items if i.category == "MANGO_REL" and not i.completed]
        habits = [i for i in all_items if i.is_habit and not i.completed]
        tasks = [i for i in all_items if i.category == "TASK" and not i.is_habit and not i.completed]

        # Estadísticas para las barras de progreso
        h_group = [i for i in all_items if i.is_habit]
        t_group = [i for i in all_items if not i.is_habit] # Tareas + Mangos

        ahora = datetime.now()
        meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "user_name": "Tatan",
            "dia_num": ahora.day,
            "mes_txt": meses[ahora.month-1],
            "fecha_friendly": f"{ahora.day} de {meses[ahora.month-1].capitalize()}",
            "saludo": "Hola",
            "mango": mango,
            "habits": habits,
            "tasks": tasks,
            "stats": {
                "h_done": len([i for i in h_group if i.completed]),
                "h_total": len(h_group),
                "t_done": len([i for i in t_group if i.completed]),
                "t_total": len(t_group)
            }
        })
    finally:
        db.close()

@app.post("/complete/{task_id}")
async def complete_task(task_id: int):
    db = SessionLocal()
    item = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if item:
        item.completed = True
        db.commit()
    db.close()
    return {"ok": True}

@app.get("/api/history/{category_type}")
async def api_history(category_type: str):
    db = SessionLocal()
    today = date.today()
    items = db.query(TaskModel).filter(TaskModel.created_at >= today, TaskModel.completed == True).all()
    if category_type == "habits":
        filtered = [i for i in items if i.is_habit]
    else:
        filtered = [i for i in items if not i.is_habit]
    db.close()
    return [{"title": i.title, "time": i.created_at.strftime("%H:%M")} for i in filtered]
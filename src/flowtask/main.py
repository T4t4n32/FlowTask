import os
import httpx
import sys
from datetime import datetime, date, timedelta
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

# --- LÓGICA DE RUTAS AUTOMÁTICA ---
# Detecta la carpeta donde está este archivo (main.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Agrega la raíz del proyecto al sistema para encontrar 'infrastructure'
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../../"))
sys.path.append(PROJECT_ROOT)

from src.flowtask.infrastructure.ai_engine import AIEngine
from src.flowtask.infrastructure.database import init_db, SessionLocal, TaskModel, save_to_db

# Cargar .env desde la raíz del proyecto
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, ".env"))

app = FastAPI()

# CONFIGURACIÓN DE TEMPLATES CORREGIDA (Ruta relativa)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

init_db()
ai_engine = AIEngine()

# --- CONFIGURACIÓN TELEGRAM ---
TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip().replace('"', '').replace("'", "")
TELEGRAM_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

async def send_telegram(chat_id: int, text: str):
    async with httpx.AsyncClient() as client:
        try:
            await client.post(TELEGRAM_URL, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
        except Exception as e:
            print(f"Error enviando a Telegram: {e}")

# --- RUTAS DEL DASHBOARD ---
@app.get("/dashboard", response_class=HTMLResponse)
async def view_dashboard(request: Request):
    db = SessionLocal()
    today = date.today()
    
    # Autolimpieza 30 días
    hace_30_dias = datetime.now() - timedelta(days=30)
    db.query(TaskModel).filter(TaskModel.created_at < hace_30_dias).delete()
    db.commit()

    try:
        all_items = db.query(TaskModel).all()
        today_items = [i for i in all_items if i.created_at.date() == today]
        
        ahora = datetime.now()
        saludo = "Buenos días" if ahora.hour < 12 else "Buenas tardes" if ahora.hour < 18 else "Buenas noches"
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        # Filtrado para las barras (Mango excluido de Tasks)
        mango_list = [i for i in today_items if i.category == "MANGO_REL" and not i.completed]
        habits_list = [i for i in today_items if i.is_habit and not i.completed]
        tasks_list = [i for i in today_items if i.category == "TASK" and not i.is_habit and not i.completed]

        h_total = [i for i in today_items if i.is_habit]
        t_total = [i for i in today_items if i.category == "TASK" and not i.is_habit]

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "user_name": "Tatan",
            "saludo": saludo,
            "fecha_friendly": f"{ahora.day} de {meses[ahora.month-1]}",
            "dia_num": ahora.day,
            "mes_txt": meses[ahora.month-1].upper(),
            "mango": mango_list,
            "habits": habits_list,
            "tasks": tasks_list,
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
    items = db.query(TaskModel).filter(TaskModel.created_at >= today).all()
    if category_type == "habits":
        filtered = [i for i in items if i.is_habit]
    else:
        filtered = [i for i in items if i.category == "TASK" and not i.is_habit]
    db.close()
    return [{"title": i.title, "status": "✅" if i.completed else "⏳", "time": i.created_at.strftime("%H:%M")} for i in filtered]

@app.post("/webhook/telegram")
async def telegram_endpoint(request: Request):
    data = await request.json()
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]
        try:
            ai_res = await ai_engine.classify_text(text)
            save_to_db(ai_res)
            icons = {"MANGO_REL": "🥭", "HABIT": "🔄", "TASK": "✅"}
            ico = icons.get(ai_res.category, "📌")
            await send_telegram(chat_id, f"{ico} *Registrado:* {ai_res.clean_title}")
        except Exception as e:
            await send_telegram(chat_id, "❌ Error al procesar.")
    return {"ok": True}
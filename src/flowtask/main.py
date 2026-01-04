import os
import httpx
import sys
from datetime import datetime, date, timedelta
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

# Configuración de Rutas
BASE_PATH = "/home/t4t4n_32/Documents/Documentos/flowtask"
sys.path.append(BASE_PATH)

from src.flowtask.infrastructure.ai_engine import AIEngine
from src.flowtask.infrastructure.database import init_db, SessionLocal, TaskModel, save_to_db

load_dotenv(dotenv_path=f"{BASE_PATH}/.env")
app = FastAPI(title="FlowTask OS - Core")
templates = Jinja2Templates(directory=f"{BASE_PATH}/src/flowtask/templates")

init_db()
ai_engine = AIEngine()

# --- UTILIDAD TELEGRAM ---
TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip().replace('"', '').replace("'", "")
TELEGRAM_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

async def send_telegram(chat_id: int, text: str):
    async with httpx.AsyncClient() as client:
        try:
            await client.post(TELEGRAM_URL, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
        except Exception as e:
            print(f"Error Telegram: {e}")

# --- DASHBOARD PRINCIPAL ---
@app.get("/dashboard", response_class=HTMLResponse)
async def view_dashboard(request: Request):
    db = SessionLocal()
    today = date.today()
    
    # 1. AUTOLIMPIEZA: Borrar registros de hace más de 30 días
    hace_30_dias = datetime.now() - timedelta(days=30)
    db.query(TaskModel).filter(TaskModel.created_at < hace_30_dias).delete()
    db.commit()

    try:
        # 2. OBTENER ITEMS DE HOY
        all_items = db.query(TaskModel).all()
        today_items = [i for i in all_items if i.created_at.date() == today]
        
        # 3. DATOS DE INTERFAZ (Saludo y Fecha)
        ahora = datetime.now()
        saludo = "Buenos días" if ahora.hour < 12 else "Buenas tardes" if ahora.hour < 18 else "Buenas noches"
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        fecha_friendly = f"{ahora.day} de {meses[ahora.month-1]}"
        mes_txt = meses[ahora.month-1].upper()

        # 4. SEGMENTACIÓN ESTRICTA (Mango no cuenta como Task en las barras)
        mango_list = [i for i in today_items if i.category == "MANGO_REL" and not i.completed]
        habits_list = [i for i in today_items if i.is_habit and not i.completed]
        tasks_list = [i for i in today_items if i.category == "TASK" and not i.is_habit and not i.completed]

        # 5. CÁLCULO DE PROGRESO (Separado)
        h_total = [i for i in today_items if i.is_habit]
        t_total = [i for i in today_items if i.category == "TASK" and not i.is_habit]

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "user_name": "Tatan",
            "saludo": saludo,
            "fecha_friendly": fecha_friendly,
            "dia_num": ahora.day,
            "mes_txt": mes_txt,
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
    try:
        item = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if item:
            item.completed = True
            db.commit()
            return {"status": "success"}
        return {"status": "not_found"}, 404
    finally:
        db.close()

@app.get("/api/history/{category_type}")
async def get_history(category_type: str):
    db = SessionLocal()
    today = date.today()
    try:
        items = db.query(TaskModel).filter(TaskModel.created_at >= today).all()
        if category_type == "habits":
            filtered = [i for i in items if i.is_habit]
        else:
            # En el historial de tareas NO mostramos los Mangos para mantener consistencia con la barra
            filtered = [i for i in items if i.category == "TASK" and not i.is_habit]
        
        return [{"title": i.title, "status": "✅" if i.completed else "⏳", "time": i.created_at.strftime("%H:%M")} for i in filtered]
    finally:
        db.close()

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
            await send_telegram(chat_id, f"{ico} *Capturado:* {ai_res.clean_title}")
        except Exception as e:
            print(f"Error: {e}")
            await send_telegram(chat_id, "❌ No pude procesar eso.")
    return {"ok": True}
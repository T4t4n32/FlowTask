import os
import httpx
import sys
import logging
from datetime import datetime, date, timedelta
from fastapi import FastAPI, Request, BackgroundTasks, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

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

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, day: str = Query(None)):
    db = SessionLocal()
    try:
        target_date = datetime.strptime(day, "%Y-%m-%d").date() if day else date.today()
        prev_day = (target_date - timedelta(days=1)).strftime("%Y-%m-%d")
        next_day = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")
        
        items = db.query(TaskModel).filter(
            TaskModel.created_at >= target_date,
            TaskModel.created_at < target_date + timedelta(days=1)
        ).all()

        # Días de la semana en español
        dias_semana = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO"]
        nombre_dia = dias_semana[target_date.weekday()]
        meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "current_date": target_date.strftime("%Y-%m-%d"),
            "dia_num": target_date.day,
            "nombre_dia": nombre_dia,
            "mes_txt": meses[target_date.month-1],
            "año": target_date.year,
            "prev_day": prev_day,
            "next_day": next_day,
            "is_today": target_date == date.today(),
            "mango": [i for i in items if i.category == "MANGO_REL" and not i.completed],
            "habits": [i for i in items if i.is_habit and not i.completed],
            "tasks": [i for i in items if i.category == "TASK" and not i.is_habit and not i.completed],
            "stats": {
                "h_done": len([i for i in items if i.is_habit and i.completed]),
                "h_total": len([i for i in items if i.is_habit]),
                "t_done": len([i for i in items if not i.is_habit and i.completed]),
                "t_total": len([i for i in items if not i.is_habit])
            }
        })
    finally: db.close()

@app.post("/complete/{task_id}")
async def complete(task_id: int):
    db = SessionLocal()
    item = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if item:
        item.completed = True
        db.commit()
    db.close()
    return {"ok": True}

@app.delete("/delete/{task_id}")
async def delete_task(task_id: int):
    db = SessionLocal()
    item = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if item:
        db.delete(item)
        db.commit()
    db.close()
    return {"ok": True}

@app.get("/api/history/{cat}")
async def history(cat: str, day: str = Query(None)):
    db = SessionLocal()
    target_date = datetime.strptime(day, "%Y-%m-%d").date() if day else date.today()
    items = db.query(TaskModel).filter(
        TaskModel.created_at >= target_date,
        TaskModel.created_at < target_date + timedelta(days=1),
        TaskModel.completed == True
    ).all()
    filtered = [i for i in items if i.is_habit] if cat == "habits" else [i for i in items if not i.is_habit]
    db.close()
    return [{"id": i.id, "title": i.title, "time": i.created_at.strftime("%H:%M")} for i in filtered]

@app.post("/webhook/telegram")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        res = await ai_engine.classify_text(data["message"]["text"])
        save_to_db(res)
        token = os.getenv("TELEGRAM_TOKEN")
        async with httpx.AsyncClient() as client:
            await client.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                              json={"chat_id": chat_id, "text": f"*{res.category}* registrado."})
    return {"ok": True}
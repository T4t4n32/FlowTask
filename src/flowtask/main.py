import os
import httpx
import sys
import logging
from datetime import datetime, date
from typing import Optional
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_

# Configuración de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../../"))
sys.path.append(PROJECT_ROOT)

from src.flowtask import teams
from src.flowtask.config import settings
from src.flowtask.infrastructure.ai_engine import AIEngine
from src.flowtask.infrastructure.database import (
    init_db,
    SessionLocal,
    TaskModel,
    get_or_create_user,
    save_to_db,
)

app = FastAPI()
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Inicialización
init_db()
ai_engine = AIEngine()

TELEGRAM_URL = f"https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}/sendMessage"

async def send_msg(chat_id: int, text: str):
    """Envía mensajes a Telegram."""
    async with httpx.AsyncClient() as client:
        try:
            await client.post(TELEGRAM_URL, json={
                "chat_id": chat_id, "text": text, "parse_mode": "Markdown"
            }, timeout=5.0)
        except Exception as e:
            logger.error(f"Error enviando a Telegram: {e}")

def get_pending_tasks_summary(user_id: int, team_id: int | None = None):
    """Resumen de tareas pendientes de hoy. Sin team_id: personales. Con team_id: de ese equipo."""
    db = SessionLocal()
    try:
        today = date.today()
        q = db.query(TaskModel).filter(
            func.date(TaskModel.created_at) == today,
            TaskModel.completed == False,
        )
        if team_id is None:
            q = q.filter(TaskModel.user_id == user_id, TaskModel.team_id.is_(None))
        else:
            q = q.filter(TaskModel.team_id == team_id)
        items = q.all()

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
async def view_dashboard(request: Request, user_id: int, date_param: Optional[str] = None):
    # user_id es obligatorio: el panel web es por-usuario (auth real llega en la Task 16).
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

        items = db.query(TaskModel).filter(
            TaskModel.user_id == user_id,
            TaskModel.team_id.is_(None),
            func.date(TaskModel.created_at) == target_date,
        ).all()
        
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
            "user_id": user_id,
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

def handle_team_command(user_id: int, text: str) -> str:
    """/equipo crear <nombre> | /equipo unir <codigo> | /equipo listar"""
    parts = text.split(maxsplit=2)
    sub = parts[1].lower() if len(parts) > 1 else ""
    arg = parts[2].strip() if len(parts) > 2 else ""

    if sub == "crear" and arg:
        t = teams.create_team(user_id, arg)
        return (
            f"🧑‍🤝‍🧑 Equipo *{t['name']}* creado.\n"
            f"Código de invitación: `{t['invite_code']}`\n"
            f"Compártelo; quien lo tenga entra con `/equipo unir {t['invite_code']}`."
        )
    if sub == "unir" and arg:
        t = teams.join_team(user_id, arg)
        if t is None:
            return "❌ Código inválido."
        return f"✅ Ya estás en el equipo *{t['name']}*."
    if sub in ("listar", "lista", ""):
        mine = teams.list_teams(user_id)
        if not mine:
            return "No estás en ningún equipo. Crea uno con `/equipo crear <nombre>`."
        lines = [
            f"- *{t['name']}* ({t['role']})" + (f" · código `{t['invite_code']}`" if t["role"] == "owner" else "")
            for t in mine
        ]
        return "🧑‍🤝‍🧑 *Tus equipos:*\n" + "\n".join(lines)
    return "Uso: `/equipo crear <nombre>` · `/equipo unir <codigo>` · `/equipo listar`"


@app.post("/webhook/telegram")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        if "message" not in data or "text" not in data["message"]:
            return {"ok": True}

        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"].strip()
        display_name = data["message"].get("from", {}).get("first_name", "")

        # Identidad = cuenta de chat. Se crea el usuario en el primer mensaje.
        user_id = get_or_create_user("telegram", chat_id, display_name)

        # --- 1. INTERCEPTOR DE COMANDOS ---
        if text.startswith("/equipo"):
            reply = handle_team_command(user_id, text)
            background_tasks.add_task(send_msg, chat_id, reply)
            return {"ok": True}

        if text.startswith("/list"):
            arg = text[len("/list"):].strip()
            if arg:
                team = teams.get_member_team_by_name(user_id, arg)
                if team is None:
                    reply = f"No estás en ningún equipo llamado *{arg}*. Usa `/equipo listar`."
                else:
                    reply = get_pending_tasks_summary(user_id, team_id=team["id"])
            else:
                reply = get_pending_tasks_summary(user_id)
            background_tasks.add_task(send_msg, chat_id, reply)
            return {"ok": True}

        # --- 2. PROCESAMIENTO DE IA ---
        ai_res = await ai_engine.classify_text(text)

        # Si es solo charla, respondemos y NO guardamos
        if ai_res.intent == "CHAT":
            response_txt = ai_res.response_text if ai_res.response_text else "🤖 Escuchando..."
            background_tasks.add_task(send_msg, chat_id, response_txt)
            return {"ok": True}

        # Si es una tarea válida (SAVE), guardamos
        save_to_db(ai_res, user_id)

        icons = {"MANGO_REL": "🥭 *MANGO*", "HABIT": "🔄 *HÁBITO*", "TASK": "✅ *TAREA*"}
        msg = f"{icons.get(ai_res.category, '📌')}\n\n*Registrado:* {ai_res.clean_title}"
        
        background_tasks.add_task(send_msg, chat_id, msg)

    except Exception as e:
        logger.error(f"Falla Webhook: {e}")
    
    return {"ok": True}

@app.post("/complete/{task_id}")
async def action_complete(task_id: int, user_id: int):
    db = SessionLocal()
    # Se completa si la tarea es del usuario (dueño) o está asignada a él en un equipo.
    item = db.query(TaskModel).filter(
        TaskModel.id == task_id,
        or_(TaskModel.user_id == user_id, TaskModel.assignee_id == user_id),
    ).first()
    team_id = None
    title = ""
    if item and not item.completed:
        item.completed = True
        team_id, title = item.team_id, item.title
        db.commit()
    db.close()

    # Avisar al dueño del equipo cuando se cierra una tarea de equipo.
    if team_id is not None:
        contact = teams.owner_contact(team_id)
        if contact and contact[0] == "telegram":
            await send_msg(int(contact[1]), f"✅ Tarea de equipo completada: *{title}*")

    return {"ok": bool(item)}

@app.get("/api/history/{category_type}")
async def get_history(category_type: str, user_id: int):
    db = SessionLocal()
    today = date.today()
    items = db.query(TaskModel).filter(
        TaskModel.user_id == user_id,
        TaskModel.created_at >= today,
        TaskModel.completed == True,
    ).all()
    if category_type == "habits":
        filtered = [i for i in items if i.is_habit]
    else:
        filtered = [i for i in items if not i.is_habit]
    db.close()
    return [{"title": i.title, "time": i.created_at.strftime("%H:%M")} for i in filtered]
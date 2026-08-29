import asyncio
import os
import re
import socket
import sys
import logging
from contextlib import asynccontextmanager
from datetime import datetime, date
from typing import Optional
from fastapi import Cookie, FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, or_

# Configuración de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../../"))
sys.path.append(PROJECT_ROOT)

from src.flowtask import convo_state, habits, nlp, pairing, poller, projects, scheduler, teams
from src.flowtask.config import settings
from src.flowtask.infrastructure.ai_engine import AIEngine
from src.flowtask.infrastructure.database import (
    complete_task,
    delete_task,
    init_db,
    postpone_task,
    SessionLocal,
    TaskModel,
    get_or_create_user,
    new_session,
    save_to_db,
    user_from_token,
)
from src.flowtask.messaging import send_message


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    poll_task = None
    if settings.TELEGRAM_POLLING:
        poll_task = asyncio.create_task(poller.run(handle_incoming_message, send_message))
    yield
    if poll_task:
        poll_task.cancel()
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Inicialización
init_db()
ai_engine = AIEngine()


def _base_url() -> str:
    if settings.PUBLIC_BASE_URL:
        return settings.PUBLIC_BASE_URL
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return f"http://{ip}:8000"


HELP = (
    "🤖 *FlowTask* — tu asistente por chat.\n\n"
    "*Escríbeme normal:*\n"
    "• `Pagar la luz mañana a las 9am` → tarea con recordatorio\n"
    "• `Leer 20 min cada día a las 22:00` → hábito diario\n"
    "• `Para <proyecto>, hacer X` → tarea dentro de un proyecto\n\n"
    "*Comandos:*\n"
    "• `/list` — tus tareas de hoy (con su `#número`)\n"
    "• `/hecho #` — marcar una tarea como hecha\n"
    "• `/posponer # <cuándo>` — mover una tarea\n"
    "• `/borrar #` — eliminar una tarea\n"
    "• `/habitos` — ver hábitos · `/habito # off|on|borrar`\n"
    "• `/proyecto` — crear un proyecto (meta → rúbrica → fecha)\n"
    "• `/proyectos` — progreso de proyectos\n"
    "• `/equipo crear|unir|listar` — equipos\n"
    "• `/ayuda` — este mensaje"
)


def _first_int(text: str):
    m = re.search(r"#?(\d+)", text)
    return int(m.group(1)) if m else None


async def handle_task_command(user_id: int, text: str) -> str:
    """/hecho, /borrar, /posponer, /habitos, /habito."""
    low = text.lower()
    tid = _first_int(text)

    if low.startswith(("/hecho", "/completar", "/done")):
        if tid is None:
            return "Uso: `/hecho #` (mira el número con `/list`)."
        res = complete_task(tid, user_id)
        if res is None:
            return f"No encuentro la tarea `#{tid}`."
        title, team_id = res
        if team_id is not None:
            contact = teams.owner_contact(team_id)
            if contact and contact[0] == "telegram":
                await send_message("telegram", contact[1],
                                   f"✅ Tarea de equipo completada: *{title}*")
        return f"✅ Hecho: *{title}*"

    if low.startswith(("/borrar", "/eliminar")):
        if tid is None:
            return "Uso: `/borrar #`."
        title = delete_task(tid, user_id)
        return f"🗑️ Borrada: *{title}*" if title else f"No encuentro la tarea `#{tid}`."

    if low.startswith(("/posponer", "/pospon", "/pospón")):
        if tid is None:
            return "Uso: `/posponer # <cuándo>` (ej. `/posponer 42 mañana 10am`)."
        cuando = re.sub(r"^\S+\s+#?\d+\s*", "", text).strip()
        due = nlp.parse_when(cuando)
        if due is None:
            return "No entendí el *cuándo*. Ej: `/posponer 42 mañana a las 10`."
        title = postpone_task(tid, user_id, due)
        if not title:
            return f"No encuentro la tarea `#{tid}`."
        return f"⏰ *{title}* movida a {due.strftime('%d/%m a las %H:%M')}"

    if low.startswith(("/habitos", "/hábitos")):
        hs = habits.list_habits(user_id)
        if not hs:
            return "No tienes hábitos. Crea uno: `Leer cada día a las 22:00`."
        out = ["🔄 *Tus hábitos:*"]
        for h in hs:
            hora = h["target_time"].strftime("%H:%M") if h["target_time"] else "sin hora"
            estado = "✅" if h["active"] else "⏸️"
            out.append(f"{estado} `#{h['id']}` {hora} — {h['title']}")
        out.append("\n_/habito # off_ · _/habito # on_ · _/habito # borrar_")
        return "\n".join(out)

    if low.startswith(("/habito", "/hábito")):
        if tid is None:
            return "Uso: `/habito # off|on|borrar`."
        if "borrar" in low or "eliminar" in low:
            title = habits.delete_habit(tid, user_id)
            return f"🗑️ Hábito borrado: *{title}*" if title else f"No encuentro el hábito `#{tid}`."
        active = "on" in low.split() or "activar" in low
        title = habits.set_active(tid, user_id, active)
        if not title:
            return f"No encuentro el hábito `#{tid}`."
        return f"{'✅ Activado' if active else '⏸️ Pausado'}: *{title}*"

    return HELP


_NO_TOKEN_HTML = (
    "<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
    "<body style='background:#000;color:#fff;font-family:system-ui;display:flex;align-items:center;"
    "justify-content:center;height:100vh;margin:0;text-align:center;padding:2rem'>"
    "<div><h2>FlowTask</h2><p>Vincula tu cuenta: manda <b>/vincular</b> a tu bot de Telegram "
    "y abre el enlace desde <b>este</b> teléfono.</p></div>"
)

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
        # ordenar por hora (las tareas sin due_at, al final)
        items = sorted(q.all(), key=lambda i: i.due_at or datetime.max)

        if not items:
            return "👍 *Todo limpio.* No tienes tareas pendientes hoy."

        def line(i):
            hora = f"{i.due_at.strftime('%H:%M')} " if i.due_at else ""
            return f"`#{i.id}` {hora}{i.title}"

        habits = [line(i) for i in items if i.is_habit]
        tasks = [line(i) for i in items if not i.is_habit]

        msg = f"📅 *Resumen del {today.strftime('%d/%m')}*\n\n"
        if habits: msg += "🔄 *HÁBITOS*\n" + "\n".join(habits) + "\n\n"
        if tasks: msg += "✅ *TAREAS*\n" + "\n".join(tasks)
        msg += "\n\n_/hecho #_ · _/posponer # <cuándo>_ · _/borrar #_"

        return msg
    finally:
        db.close()

@app.get("/app")
def pair_and_open(code: str):
    """El celular abre este enlace (de /vincular): canjea el código por una cookie de sesión."""
    if not settings.WEB_ENABLED:
        return HTMLResponse("Panel web desactivado.", 404)
    uid = pairing.consume(code)
    if uid is None:
        return HTMLResponse("Código inválido o caducado. Pide otro con /vincular en el bot.", 400)
    resp = RedirectResponse("/dashboard", status_code=302)
    resp.set_cookie(
        "ft_token", new_session(uid),
        max_age=31_536_000, httponly=True, samesite="lax", path="/",
    )
    return resp


@app.get("/dashboard", response_class=HTMLResponse)
async def view_dashboard(
    request: Request, date_param: Optional[str] = None, ft_token: Optional[str] = Cookie(None)
):
    if not settings.WEB_ENABLED:
        return HTMLResponse("Panel web desactivado. FlowTask funciona por Telegram.", 404)
    user_id = user_from_token(ft_token)
    if user_id is None:
        return HTMLResponse(_NO_TOKEN_HTML, status_code=200)
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
        ).order_by(TaskModel.due_at.is_(None), TaskModel.due_at).all()
        
        habits = [i for i in items if i.is_habit and not i.completed]
        tasks = [i for i in items if not i.is_habit and not i.completed]

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


# "Para <proyecto>, <tarea>"  /  "Para <proyecto>: <tarea>"
_PARA_RE = re.compile(r"^para\s+(.+?)\s*[,:]\s*(.+)$", re.IGNORECASE | re.DOTALL)


def _parse_deadline(text: str):
    text = text.strip()
    try:
        return date.fromisoformat(text)
    except ValueError:
        pass
    dt = nlp.parse_when(text)
    return dt.date() if dt else None


def _format_projects(rows: list[dict]) -> str:
    if not rows:
        return "No tienes proyectos. Crea uno con `/proyecto`."
    out = ["🗂️ *Tus proyectos:*"]
    for p in rows:
        out.append(
            f"• *{p['title']}* — {p['done']}/{p['total']} · límite {p['deadline'].strftime('%d/%m')}"
        )
        for quien, frac in p.get("by_person", {}).items():
            out.append(f"    ↳ {quien}: {frac}")
    return "\n".join(out)


async def _generate_and_confirm(
    platform, chat_id, user_id, goal, rubric, deadline, team_id=None
) -> str:
    tasks = await ai_engine.decompose_goal(goal, rubric, deadline)
    convo_state.set(
        platform, chat_id,
        {"step": "confirm", "goal": goal, "rubric": rubric, "deadline": deadline,
         "tasks": tasks, "team_id": team_id},
    )
    plan = "\n".join(f"• {t.due_date.strftime('%d/%m')} — {t.title}" for t in tasks)
    destino = " (equipo)" if team_id else ""
    return (
        f"🗂️ *Plan para «{goal}»*{destino} (límite {deadline.strftime('%d/%m/%Y')}):\n{plan}\n\n"
        "Responde *aceptar* o *regenerar* (o *cancelar*)."
    )


async def _finish_deadline(platform, chat_id, user_id, st, dl):
    """Tras la fecha: si el usuario tiene equipos, pregunta destino; si no, genera el plan."""
    st.update(step="team", deadline=dl)
    if not teams.list_teams(user_id):
        return await _generate_and_confirm(
            platform, chat_id, user_id, st["goal"], st["rubric"], dl
        )
    return "👥 ¿Para un equipo? Escribe el nombre del equipo, o *no* para personal."


async def handle_project_flow(platform, chat_id, user_id: int, text: str) -> str:
    """Asistente de `/proyecto`: meta → rúbrica → fecha → (equipo) → confirmar."""
    st = convo_state.get(platform, chat_id)
    low = text.strip().lower()

    # /proyecto (re)inicia el flujo
    if text.startswith("/proyecto"):
        convo_state.clear(platform, chat_id)
        arg = text[len("/proyecto"):].strip()
        parts = [p.strip() for p in arg.split("|")]
        if len(parts) in (3, 4) and all(parts[:3]):
            dl = _parse_deadline(parts[2])
            if dl is None:
                return "No entendí la fecha límite. Usa formato *2026-09-15*."
            team_id = None
            if len(parts) == 4 and parts[3]:
                team = teams.get_member_team_by_name(user_id, parts[3])
                if team is None:
                    return f"No estás en ningún equipo llamado *{parts[3]}*."
                team_id = team["id"]
            return await _generate_and_confirm(
                platform, chat_id, user_id, parts[0], parts[1], dl, team_id
            )
        if arg:
            convo_state.set(platform, chat_id, {"step": "rubric", "goal": arg})
            return "📋 Meta anotada. ¿Rúbrica de evaluación? (o escribe *ninguna*)"
        convo_state.set(platform, chat_id, {"step": "goal"})
        return "🎯 ¿Cuál es la meta del proyecto?"

    if st is None:
        return "Empieza con `/proyecto`."
    if low in ("/cancelar", "cancelar"):
        convo_state.clear(platform, chat_id)
        return "❌ Proyecto cancelado."

    step = st["step"]
    if step == "goal":
        st.update(step="rubric", goal=text.strip())
        return "📋 ¿Rúbrica de evaluación? (o escribe *ninguna*)"
    if step == "rubric":
        st.update(step="deadline", rubric="" if low in ("ninguna", "no", "-") else text.strip())
        return "📅 ¿Fecha límite? (ej. *2026-09-15* o «15 de septiembre»)"
    if step == "deadline":
        dl = _parse_deadline(text)
        if dl is None:
            return "No entendí la fecha. Prueba con formato *2026-09-15*."
        return await _finish_deadline(platform, chat_id, user_id, st, dl)
    if step == "team":
        team_id = None
        if low not in ("no", "-", "ninguno", "personal"):
            team = teams.get_member_team_by_name(user_id, text)
            if team is None:
                return "No estás en ese equipo. Escribe el nombre exacto o *no*."
            team_id = team["id"]
        return await _generate_and_confirm(
            platform, chat_id, user_id, st["goal"], st["rubric"], st["deadline"], team_id
        )
    if step == "confirm":
        if low in ("aceptar", "ok", "si", "sí", "dale"):
            res = projects.create_project(
                user_id, st["goal"], st["rubric"], st["deadline"], st["tasks"],
                team_id=st.get("team_id"),
            )
            convo_state.clear(platform, chat_id)
            await _notify_assignees(platform, res)
            return (
                f"✅ Proyecto *{res['title']}* creado con {res['n_tasks']} tareas. "
                "Sus recordatorios ya están activos."
            )
        if low in ("regenerar", "otra", "otro", "de nuevo"):
            return await _generate_and_confirm(
                platform, chat_id, user_id, st["goal"], st["rubric"], st["deadline"],
                st.get("team_id"),
            )
        return "Responde *aceptar* o *regenerar* (o *cancelar*)."

    convo_state.clear(platform, chat_id)
    return "Algo se enredó. Empieza de nuevo con `/proyecto`."


async def _notify_assignees(platform, res: dict) -> None:
    assignments = res.get("assignments") or {}
    if not assignments:
        return
    contacts = projects.contacts_for(list(assignments.keys()))
    for uid, titles in assignments.items():
        c = contacts.get(uid)
        if not c:
            continue
        body = f"📌 Tu parte de *{res['title']}*:\n" + "\n".join(f"• {t}" for t in titles)
        await send_message(c[0], c[1], body)


async def handle_incoming_message(
    platform: str, chat_id, text: str, display_name: str = ""
) -> str:
    """Núcleo agnóstico de plataforma: recibe un mensaje, devuelve la respuesta a enviar."""
    text = text.strip()
    # Identidad = cuenta de chat. Se crea el usuario en el primer mensaje.
    user_id = get_or_create_user(platform, chat_id, display_name)

    # --- 1. COMANDOS ---
    if text.startswith(("/start", "/ayuda", "/help")):
        return HELP

    if text.startswith(
        ("/hecho", "/completar", "/done", "/borrar", "/eliminar",
         "/posponer", "/pospon", "/pospón", "/habito", "/hábito")
    ):
        return await handle_task_command(user_id, text)

    if text.startswith("/vincular") or text.startswith("/app"):
        if not settings.WEB_ENABLED:
            return "El panel web está desactivado por ahora. Usa el chat."
        code = pairing.new_code(user_id)
        return (
            f"🔗 Abre esto en tu celular (misma WiFi):\n{_base_url()}/app?code={code}\n\n"
            "El enlace vale 10 minutos. Luego «Agregar a pantalla de inicio»."
        )

    if text.startswith("/proyectos"):
        return _format_projects(projects.list_projects(user_id))

    if text.startswith("/proyecto") or convo_state.get(platform, chat_id) is not None:
        return await handle_project_flow(platform, chat_id, user_id, text)

    if text.startswith("/equipo"):
        return handle_team_command(user_id, text)

    if text.startswith("/list"):
        arg = text[len("/list"):].strip()
        if not arg:
            return get_pending_tasks_summary(user_id)
        team = teams.get_member_team_by_name(user_id, arg)
        if team is None:
            return f"No estás en ningún equipo llamado *{arg}*. Usa `/equipo listar`."
        return get_pending_tasks_summary(user_id, team_id=team["id"])

    # --- 2. "Para <proyecto>, <tarea>" → tarea dentro de ese proyecto ---
    m = _PARA_RE.match(text)
    if m:
        proj = projects.find_by_name(user_id, m.group(1).strip())
        if proj is not None:
            tarea = m.group(2).strip()
            due_at = nlp.parse_when(tarea)
            titulo = nlp.strip_when(tarea)
            projects.add_task(proj["id"], user_id, titulo, due_at)
            extra = f" ⏰ {due_at.strftime('%d/%m %H:%M')}" if due_at else ""
            return f"📁 Añadido a *{proj['title']}*: {titulo}{extra}"
        # Sin proyecto con ese nombre: seguir con el texto tras la coma como tarea normal.
        text = m.group(2).strip()

    # --- 3. IA ---
    ai_res = await ai_engine.classify_text(text)

    if ai_res.intent == "CHAT":
        return ai_res.response_text or "🤖 Escuchando..."

    # SAVE: tarea o hábito
    due_at = nlp.parse_when(text)
    if ai_res.is_habit:
        habits.create_habit(user_id, ai_res.clean_title, due_at.time() if due_at else None)
        msg = f"🔄 *Hábito* registrado: {ai_res.clean_title}"
        if due_at:
            msg += f"\n⏰ cada día a las {due_at.strftime('%H:%M')}"
        return msg

    save_to_db(ai_res, user_id, due_at)
    msg = f"✅ *Registrado:* {ai_res.clean_title}"
    if due_at:
        msg += f"\n⏰ para el {due_at.strftime('%d/%m a las %H:%M')}"
    return msg


@app.post("/webhook/telegram")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    """Adaptador fino: parsea el payload de Telegram y delega en el núcleo."""
    # En modo polling el webhook no se usa; dejarlo abierto permitiría inyectar mensajes falsos.
    if settings.TELEGRAM_POLLING:
        return {"ok": True}
    try:
        msg = (await request.json()).get("message", {})
        if "text" not in msg:
            return {"ok": True}
        chat_id = msg["chat"]["id"]
        name = msg.get("from", {}).get("first_name", "")
        reply = await handle_incoming_message("telegram", chat_id, msg["text"], name)
        if reply:
            background_tasks.add_task(send_message, "telegram", chat_id, reply)
    except Exception as e:
        logger.error(f"Falla Webhook: {e}")
    return {"ok": True}

@app.post("/complete/{task_id}")
async def action_complete(task_id: int, ft_token: Optional[str] = Cookie(None)):
    user_id = user_from_token(ft_token)
    if user_id is None:
        return {"ok": False, "auth": False}
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
            await send_message("telegram", contact[1], f"✅ Tarea de equipo completada: *{title}*")

    return {"ok": bool(item)}

@app.get("/api/history/{category_type}")
async def get_history(category_type: str, ft_token: Optional[str] = Cookie(None)):
    user_id = user_from_token(ft_token)
    if user_id is None:
        return []
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
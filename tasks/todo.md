# FlowTask — Task List

Comandos del repo:
- Tests: `pytest tests/ -q`
- Lint: `ruff check .`
- Run local: `uvicorn src.flowtask.main:app --reload`
- Migraciones: `alembic upgrade head`

---

## Fase 0: Fundaciones

Progreso: [x] Task 1  ·  [~] Task 2 (código hecho; falta que TÚ crees Supabase/Railway)

### Task 1: Limpieza del repo y saneo de dependencias — HECHA (2026-08-28)

**Description:** Aplicar la auditoría ponytail: borrar el scaffold clean-architecture muerto y dejar
`requirements.txt` / `pyproject.toml` con lo que realmente se usa, para no arrastrar peso a las fases
siguientes.

**Acceptance criteria:**
- [x] Borrados `src/flowtask/{api,core,domain}/`, `infrastructure/firebase.py`, `infrastructure/telegram.py`, `verify_db.py`, `verify_flow.py`, `test_ia.py`, `Makefile`
- [x] `requirements.txt` reducido a lo que hoy se importa: fastapi, uvicorn, httpx, pydantic, sqlalchemy, jinja2, python-dotenv. Las deps de fases futuras (apscheduler, alembic, psycopg, dateparser) las añade la task que las use.
- [x] `pyproject.toml` sin `python-jose`, `passlib`, `firebase-admin`, `python-telegram-bot`, `pydantic-settings`, `dateparser`
- [x] `.gitignore`: `.agents/` y `.claude/skills/` (skills se instalan por máquina, no se versionan)
- [x] Verificado por análisis estático: todo `import` en el código vivo resuelve a stdlib, a las 7 deps declaradas o al paquete local

**Verification:**
- [x] `venv` creado + `pip install -r requirements.txt` OK (Python 3.14, todas las libs con wheel)
- [x] `python -c "from src.flowtask.main import app"` importa sin error (8 rutas)
- [x] `uvicorn src.flowtask.main:app` arranca: "Application startup complete"
- [x] `GET /dashboard` responde 200 y renderiza (`<title>FlowTask OS</title>`, "AGOSTO", "Hábitos")
- [ ] PENDIENTE (necesita webhook público): mensaje real de Telegram end-to-end
- [ ] `ruff check .` — no instalado; se cubre en Task 20

**Bug encontrado y arreglado durante la verificación:** `main.py` usaba la firma vieja
`templates.TemplateResponse("dashboard.html", {...})`, que la versión actual de Starlette ya no acepta
(rompía con error 500). Cambiado a la firma nueva `TemplateResponse(request, "dashboard.html", {...})`.
No lo causó la limpieza; salió a la luz al reinstalar deps sin pinear.

**Dependencies:** None
**Files likely touched:** `requirements.txt`, `pyproject.toml`, `.gitignore`, `src/flowtask/main.py`, (borrados)
**Estimated scope:** Small
**Nota:** `.github/workflows/ci.yml` y `.pre-commit-config.yaml` siguen rotos (referencian `backend/src`,
black, flake8, isort). Se reescriben en la Task 20, no aquí.

---

### Task 2: Provisionar Supabase + Railway y centralizar configuración — CÓDIGO HECHO (2026-08-28)

**Description:** Crear el proyecto Supabase y el proyecto Railway. Un único módulo de settings que lea
todas las variables de entorno (hoy están repartidas entre `main.py`, `ai_engine.py`, `database.py`).

**Acceptance criteria:**
- [x] `src/flowtask/config.py` expone `settings` (TELEGRAM_TOKEN, GEMINI_API_KEY, GEMINI_MODEL, DATABASE_URL); `main.py`/`ai_engine.py`/`database.py` lo importan en vez de `os.getenv` suelto
- [x] `.env.example` con todas las claves y de dónde sacar cada una
- [x] `database.py`: `check_same_thread` solo si es SQLite (no rompe con Postgres); `declarative_base` importado del sitio no-deprecado
- [ ] **TÚ:** crear proyecto en Supabase → copiar la connection string del *Transaction pooler* (6543) y la contraseña → guardarlas en una nota. **NO ponerlas en `.env` todavía** (rompería la app hasta la Task 3, que instala el driver de Postgres). Por ahora `DATABASE_URL` se deja vacío = SQLite.
- [ ] **TÚ:** crear el archivo `.env` (copia de `.env.example`) y rellenar `TELEGRAM_TOKEN` y `GEMINI_API_KEY`. `DATABASE_URL` vacío.
- [ ] **TÚ:** crear proyecto en Railway (opcional ahora; también se puede dejar para la Task 19)

**Verification:**
- [x] `python -c "from src.flowtask.config import settings; print(settings.DATABASE_URL)"` → `sqlite:///./flowtask.db`
- [x] App arranca; `/dashboard` responde 200; sin errores en el log
- [ ] **TÚ (tras crear el `.env`):** volver a arrancar y confirmar que sigue OK

**Dependencies:** Task 1
**Files likely touched:** `src/flowtask/config.py`, `src/flowtask/main.py`, `src/flowtask/infrastructure/ai_engine.py`, `src/flowtask/infrastructure/database.py`, `.env.example`
**Estimated scope:** Small
**Skills:** `use-railway`, `supabase-postgres-best-practices`
**Nota:** el código no necesita la URL real de Supabase todavía — por defecto usa SQLite y todo
funciona. La URL de Supabase entra en juego de verdad en la Task 3.

---

## Fase 1: Postgres multiusuario + equipos

Progreso: [x] Task 3  ·  [x] Task 4  ·  [x] Task 5  ·  [x] Task 6  — Fase 1 COMPLETA

### Task 3: Migrar SQLAlchemy de SQLite a Supabase Postgres + Alembic — HECHA (2026-08-29)

**Description:** Cambiar el engine a Postgres, añadir `psycopg`, introducir Alembic y crear la
migración inicial que reproduce el `tasks` actual. Sin cambios de comportamiento todavía.

**Acceptance criteria:**
- [x] `database.py`: normaliza `postgresql://` → `postgresql+psycopg://`; SQLite mantiene `check_same_thread`; Postgres usa `pool_pre_ping=True`, `pool_size=5`, `max_overflow=2`, `prepare_threshold=None` (compatible con el transaction pooler de Supabase)
- [x] `alembic init migrations` hecho; `migrations/env.py` toma la URL de `settings` y `Base.metadata`; `alembic.ini` con `sqlalchemy.url` vacío
- [x] Migración `0001_initial` crea `tasks` con las mismas columnas + índice `ix_tasks_id`
- [x] `init_db()` ahora llama a `alembic upgrade head` (documentado en README, sección "Puesta en marcha")
- [x] `alembic check` → "No new upgrade operations detected" (modelo y migración en sync)
- [x] `alembic upgrade head` contra Supabase OK (tras resetear la password de la BD sin símbolos)

**Verification:**
- [x] `alembic upgrade head` / `downgrade base` / `upgrade head` en bucle: sin error (SQLite local)
- [x] App arranca; `init_db()` aplica la migración; `/dashboard` → 200
- [x] `alembic upgrade head` contra Supabase: tablas `tasks` y `alembic_version` visibles en el Table Editor
      Luego mandar un mensaje al bot y ver la fila aparecer.

**Dependencies:** Task 2
**Files likely touched:** `src/flowtask/infrastructure/database.py`, `alembic.ini`, `migrations/` (env.py, script.py.mako, versions/0001_initial.py), `README.md`, `requirements.txt`, `pyproject.toml`
**Estimated scope:** Medium
**Skills:** `supabase-postgres-best-practices`

---

### Task 4: Multiusuario — `users`, `tasks.user_id`, aislamiento — CÓDIGO HECHO (2026-08-29)

**Description:** Añadir tabla `users` (id, platform, chat_id, display_name, created_at; único por
`(platform, chat_id)`). En cada mensaje entrante, upsert del usuario. `tasks.user_id` FK NOT NULL.
**Toda** query de `main.py` (`get_pending_tasks_summary`, `view_dashboard`, `get_history`,
`action_complete`) pasa a filtrar por `user_id`.

**Acceptance criteria:**
- [x] Migración `0002_users`: tabla `users` (único `(platform, chat_id)`) + `tasks.user_id` FK NOT NULL + índice `ix_tasks_user_created (user_id, created_at)`. Usa `batch_alter_table` → funciona en SQLite y Postgres. `alembic check` limpio.
- [x] `get_or_create_user("telegram", chat_id, display_name)` en el webhook antes de clasificar
- [x] `save_to_db(ai_res, user_id)` guarda el dueño; todas las queries de `main.py` filtran por `user_id`
- [x] `action_complete` solo completa si `task.user_id == user_id` (devuelve `{"ok": false}` si no)
- [x] `/dashboard`, `/complete`, `/api/history` ahora exigen `?user_id=` (auth real en Task 16); el template pasa el `user_id` en cada fetch
- [x] `cli_manager.py`: columna USER en el monitor

**Verification:**
- [x] `pytest tests/test_isolation.py` → 4 passed (idempotencia, aislamiento por plataforma, resumen no cruzado, no completar tarea ajena)
- [x] `0002` aplicado a Supabase (`alembic upgrade head`) y en SQLite (vía `init_db()` en los tests)
- [x] Server smoke: `/dashboard` sin `user_id` → 422; con `?user_id=1` → 200
- [ ] **TÚ (manual):** dos cuentas de Telegram reales, `/list` de cada una no se cruza (requiere webhook público / Task 19)

**Dependencies:** Task 3
**Files likely touched:** `src/flowtask/infrastructure/database.py`, `src/flowtask/main.py`, `migrations/versions/0002_users.py`, `tests/test_isolation.py`
**Estimated scope:** Medium
**Skills:** `supabase-postgres-best-practices`, `pytest`

---

### Task 5: Equipos — `teams`, `team_members`, `tasks.team_id/assignee_id` — HECHA (2026-08-29)

**Description:** Modelo de equipos: `teams` (id, name, owner_id, invite_code), `team_members`
(team_id, user_id, role — PK compuesta). `tasks` gana `team_id` NULL y `assignee_id` NULL.
Comandos de chat `/equipo crear|unir|listar`.

**Acceptance criteria:**
- [x] Migración `0003_teams`: `teams`, `team_members` (PK compuesta `(team_id, user_id)`), `tasks.team_id`, `tasks.assignee_id`. `alembic check` limpio. Aplicada a Supabase y SQLite.
- [x] `src/flowtask/teams.py`: `create_team`, `join_team` (idempotente, code inválido → None), `list_teams`, `get_member_team_by_name`, `owner_contact`
- [x] `/equipo crear <nombre>` → crea equipo + código; `/equipo unir <codigo>` → se une; `/equipo listar` → sus equipos (nota: se usa `unir` en vez de `invitar` del plan; más claro para quien pega el código)
- [x] `/list` = personales (`team_id IS NULL`); `/list <nombre-equipo>` = tareas de ese equipo (si es miembro)
- [x] `action_complete`: un miembro asignado puede cerrar la tarea de equipo; al cerrarse, se notifica al dueño del equipo por Telegram
- [x] `view_dashboard` sigue mostrando solo tareas personales (`team_id IS NULL`)

**Verification:**
- [x] `pytest` → 9 passed (4 isolation + 5 teams: crear/unir idempotente, code inválido, no-miembro no ve el equipo, miembro asignado completa)
- [x] Smoke: webhook `/equipo crear` crea equipo con dueño como miembro `owner`; `/list` y dashboard OK
- [ ] **TÚ (manual):** flujo de invitación real entre dos cuentas de Telegram (requiere webhook público / Task 19)

**Dependencies:** Task 4
**Files likely touched:** `src/flowtask/infrastructure/database.py`, `src/flowtask/main.py`, `src/flowtask/teams.py`, `migrations/versions/0003_teams.py`, `tests/test_teams.py`
**Estimated scope:** Medium

---

### Task 6: RLS en Supabase (deny-by-default) — HECHA (2026-08-29)

**Description:** Activar RLS en `tasks`, `users`, `teams`, `team_members` como defensa en profundidad.

**Ajuste vs plan original:** las políticas por `auth.uid()` se posponen a la Task 15/16. Motivo: no
hay Supabase Auth todavía; `users` no tiene columna que comparar con `auth.uid()`. Escribir esas
políticas ahora sería contra columnas inexistentes. Lo que sí aporta valor hoy = **deny-by-default**.

**Acceptance criteria:**
- [x] `0004_rls`: `ENABLE ROW LEVEL SECURITY` en las 4 tablas, **sin políticas permisivas** → `anon`/`authenticated` ven 0 filas y no escriben. No-op en SQLite. `alembic check` limpio. Aplicada a Supabase (`0004_rls (head)`).
- [x] Backend intacto: conecta como `postgres` (dueño de las tablas) → bypasea RLS. No se usa `FORCE ROW LEVEL SECURITY`.
- [x] Documentado en README (sección "Seguridad de datos (RLS)")
- [~] Políticas `select/insert/update` por `auth.uid()` → **movidas a Task 15/16**

**Verification:**
- [x] `RLS_TEST=1 pytest tests/test_rls.py` → 2 passed contra Supabase (todo en transacción con rollback, no toca datos):
      - con RLS + fila real + `GRANT SELECT ... TO authenticated`, el rol `authenticated` ve **0 filas**
      - el rol por defecto (backend) sigue leyendo/escribiendo
- [x] `pytest -q` normal: 9 passed, 2 skipped (RLS es opt-in con `RLS_TEST=1`)
- [ ] **TÚ (manual, opcional):** en Supabase → Table Editor, cada tabla muestra el candado "RLS enabled"

**Dependencies:** Task 5
**Files likely touched:** `migrations/versions/0004_rls.py`, `tests/test_rls.py`, `README.md`
**Estimated scope:** Small (reducido: sin políticas por auth.uid() todavía)
**Skills:** `supabase-postgres-best-practices`

### Checkpoint: Fase 1 — COMPLETA (2026-08-29)
- [x] `pytest -q` verde (9 passed, 2 skipped)
- [x] `alembic upgrade head` limpio desde cero (SQLite y Supabase, hasta `0004_rls`)
- [ ] **TÚ (manual, Task 19):** dos cuentas de Telegram reales sin cruce; flujo de equipo end-to-end
- [ ] **Revisión con humano** antes de la Fase 2

---

## Fase 2: Fechas naturales + recordatorios

Progreso: [x] Task 7  ·  [x] Task 8  ·  [x] Task 9  — Fase 2 COMPLETA

### Task 7: Parser de fecha/hora en español + `due_at` / `reminder_sent` — CÓDIGO HECHO (2026-08-29)

**Description:** Wire de `dateparser`. Helper `parse_when(text, now=None) -> datetime | None`.
`tasks` gana `due_at` (nullable) y `reminder_sent` (bool, server_default 0). Al guardar se extrae
`due_at`; el bot confirma la fecha interpretada.

**Acceptance criteria:**
- [x] `src/flowtask/nlp.py`: `parse_when()` con `search_dates(languages=["es"], PREFER_DATES_FROM="future")` + `_normalize()` que traduce "a las 9" / "9am" / "9 de la noche" a "HH:00" (dateparser 1.4.x no las pilla solo)
- [x] Migración `0005_due_at`: `tasks.due_at`, `tasks.reminder_sent` + índice `ix_tasks_due_pending (due_at, reminder_sent)` (para el barrido de la Task 8). `alembic check` limpio.
- [x] Mensaje sin fecha → `due_at = NULL`, flujo intacto
- [x] Respuesta del bot: `⏰ para el DD/MM a las HH:MM` cuando hay `due_at`
- [x] Prompt de la IA: `clean_title` "SIN fechas ni horas"
- [x] `dateparser` añadido a requirements.txt / pyproject.toml
- [x] `0005` aplicada a Supabase (`0005_due_at (head)`; `due_at TIMESTAMP`, `reminder_sent BOOLEAN`). Bug corregido: `server_default` era `0` (SQLite ok, Postgres no) → `false`.

**Verification:**
- [x] `pytest tests/test_nlp.py` → 11 passed (mañana 9am, viernes 4pm, 15:30, 7 de la mañana, 9 de la noche, "5 de septiembre", "en 2 horas", sin-fecha→None, prefiere futuro)
- [x] `pytest -q` total: 20 passed, 2 skipped
- [x] Smoke: webhook con "Pagar la factura de la luz mañana a las 9am" → fila con `due_at = 2026-08-30 09:00`; "Comprar pan" → `due_at = NULL`
- [ ] **TÚ (manual):** mandar "Pagar luz mañana 9am" al bot y ver la confirmación con la hora

**Ceiling (`ponytail:`):** dateparser no combina "el viernes" + "a las 4" si van separados en frases
largas → puede quedar la fecha sin hora. El bot confirma la interpretación para que corrijas.

**Dependencies:** Task 4
**Files likely touched:** `src/flowtask/nlp.py`, `src/flowtask/infrastructure/ai_engine.py`, `src/flowtask/infrastructure/database.py`, `src/flowtask/main.py`, `migrations/versions/0005_due_at.py`, `tests/test_nlp.py`, `requirements.txt`, `pyproject.toml`
**Estimated scope:** Medium
**Skills:** `pytest`

---

### Task 8: Scheduler + barrido de recordatorios — HECHA (2026-08-29)

**Description:** `AsyncIOScheduler` que arranca con la app (lifespan). Un job cada 60 s:
`tasks WHERE due_at <= now() AND reminder_sent = false AND completed = false` → recordatorio al
chat del usuario → `reminder_sent = true` (solo si el envío fue OK).

**Ajuste vs plan:** **sin `SQLAlchemyJobStore`**. El único job (`reminder_sweep`) es código y se
re-registra en cada arranque con `replace_existing=True`; el barrido recupera lo atrasado tras un
reinicio por sí solo. Un jobstore persistente para un solo cron job es YAGNI (y evita las tablas de
APScheduler en la BD + líos de pickle/pooler).

**Acceptance criteria:**
- [x] `scheduler.start()` en el `lifespan` de FastAPI; `scheduler.shutdown()` al cerrar
- [x] Job `reminder_sweep` con `id="reminder_sweep"`, `replace_existing=True`, `max_instances=1`, `coalesce=True`
- [x] `src/flowtask/messaging.py` (nuevo): `send_message(platform, chat_id, text) -> bool`; el sweep lo usa según `user.platform`
- [x] `max_instances=1` evita solape (con 1 réplica basta; `pg_advisory_lock` marcado como upgrade para multi-réplica)
- [x] `reminder_sent = True` solo si `send_message` devolvió True (si falla, se reintenta al siguiente barrido)
- [x] `main.py`: los 5 puntos de envío pasan a `send_message("telegram", ...)`; `send_msg`/`TELEGRAM_URL`/`httpx` salen de `main.py`

**Verification:**
- [x] `pytest tests/test_scheduler.py` → 5 passed (vencida dispara, no se repite, futura no, completada no, envío fallido no marca)
- [x] `pytest -q` total: 25 passed, 2 skipped
- [x] Smoke: al arrancar uvicorn → log "Scheduler arrancado (reminder_sweep cada 60s)"; dashboard 200
- [ ] **TÚ (manual):** "recordar test en 2 minutos" al bot, esperar → llega el mensaje (requiere webhook público / Task 19)

**Nota TZ:** `due_at` y `datetime.now()` son naive (hora local del server). En Railway hay que fijar `TZ` (Task 19).
**Sin migración** (la columna `reminder_sent` la creó `0005`).

**Dependencies:** Task 7
**Files likely touched:** `src/flowtask/scheduler.py`, `src/flowtask/messaging.py`, `src/flowtask/main.py`, `requirements.txt`, `pyproject.toml`, `tests/test_scheduler.py`
**Estimated scope:** Medium
**Skills:** `cron-scheduling`, `reminder-scheduler`

---

### Task 9: Hábitos recurrentes + hora visible en `/list` y dashboard — HECHA (2026-08-29)

**Description:** Tabla `habits` (definición del hábito). Job diario 00:05 que genera la instancia del
día en `tasks`. `/list` y dashboard muestran la hora y ordenan por `due_at`.

**Acceptance criteria:**
- [x] Migración `0006_habits`: tabla `habits` (user_id, title, target_time, active) + `tasks.habit_id` FK. `alembic check` limpio. Aplicada a Supabase (`0006_habits (head)`).
- [x] `src/flowtask/habits.py`: `create_habit` (alta + genera la instancia de hoy), `rollover_habits` (idempotente, salta inactivos), `_ensure_today_instance`
- [x] Webhook: si `ai_res.is_habit` → `habits.create_habit(...)` con la hora extraída por `nlp`; si no, tarea normal
- [x] Scheduler: job `habit_rollover` (`cron` 00:05, `id` fijo, `replace_existing`)
- [x] `get_pending_tasks_summary` ordena por `due_at` y prefija `HH:MM`
- [x] `dashboard.html` + query: cada ítem muestra `HH:MM` si tiene `due_at`, ordenados por hora

**Verification:**
- [x] `pytest tests/test_habits.py` → 5 passed (alta genera instancia de hoy, rollover no duplica, rollover crea la del día, hábito inactivo no se regenera, `/list` muestra la hora)
- [x] `pytest -q` total: 32 passed, 2 skipped
- [x] Smoke: webhook "leer ... cada día a las 17:00" → fila en `habits` + instancia en `tasks` con `is_habit`, `category=HABIT`, `habit_id`; dashboard 200; scheduler registra `habit_rollover`
- [ ] **TÚ (manual):** crear hábito con hora, al día siguiente aparece con recordatorio (requiere webhook público / Task 19)

**Bug arreglado de paso:** aislamiento entre archivos de test (todos compartían BD por el `os.environ`
en cada módulo). Ahora hay `tests/conftest.py` con BD única + limpieza de tablas entre tests.
**`nlp.parse_when` mejorado:** quita "cada día / todos los días", entiende "17hs", y elige el último
match ignorando duraciones sueltas ("15 min") → "leer 15 min cada día a las 17:00" ahora da 17:00.

**Dependencies:** Task 8
**Files likely touched:** `src/flowtask/habits.py`, `src/flowtask/scheduler.py`, `src/flowtask/nlp.py`, `src/flowtask/main.py`, `src/flowtask/infrastructure/database.py`, `src/flowtask/templates/dashboard.html`, `migrations/versions/0006_habits.py`, `tests/conftest.py`, `tests/test_habits.py`, `tests/test_nlp.py`
**Estimated scope:** Medium

### Checkpoint: Fase 2 — COMPLETA (2026-08-29)
- [x] `pytest -q` verde (32 passed, 2 skipped)
- [x] Migraciones al día en Supabase (`0006_habits`)
- [ ] **TÚ (manual, Task 19):** un recordatorio real llega al chat a la hora fijada
- [ ] **TÚ (manual, Task 19):** un hábito se regenera y recuerda al día siguiente
- [ ] **Revisión con humano** antes de la Fase 3

---

## Fase 3: Preparar multi-canal (sin coste)

Progreso: [x] Task 10  ·  [~] Task 11 DIFERIDA (WhatsApp, hasta publicar)

### Task 10: Refactor a núcleo agnóstico de plataforma — HECHA (2026-08-29)

**Description:** Extraer del `telegram_webhook` toda la lógica no-Telegram a
`handle_incoming_message(platform, chat_id, text, display_name) -> reply_text`.

**Acceptance criteria:**
- [x] `handle_incoming_message` (en `main.py`) no toca nada de Telegram: resuelve usuario, enruta `/equipo` y `/list`, llama a la IA, guarda tarea/hábito, devuelve el string de respuesta
- [x] `send_message(platform, chat_id, text)` (en `messaging.py`, desde Task 8) decide el transporte por `platform`
- [x] `telegram_webhook` es un adaptador fino: parsea el payload → `handle_incoming_message("telegram", ...)` → `background_tasks.add_task(send_message, "telegram", chat_id, reply)`
- [x] `background_tasks` sigue usándose para el envío de la respuesta

**Verification:**
- [x] `pytest -q`: 38 passed, 2 skipped (los 32 previos sin cambios de assert + 6 nuevos de `test_handler`)
- [x] `test_handler.py`: comando de equipo no llama a la IA; `/list` vacío; guardar tarea; charla; hábito; **el mismo mensaje por `platform="whatsapp"` da la misma respuesta que por `"telegram"`**
- [x] Smoke: webhook de Telegram con `/equipo`, `/list`, mensaje libre → todo `{"ok":true}`, dashboard 200, sin errores

**Añadir un canal nuevo (WhatsApp, etc.) = solo:** un endpoint `/webhook/<canal>` que parsee su payload
y llame a `handle_incoming_message("<canal>", ...)`, + una rama en `send_message`. La lógica no se toca.

**Dependencies:** Task 8
**Files likely touched:** `src/flowtask/main.py`, `tests/test_handler.py`
**Estimated scope:** Medium

---

### Task 11: Integración WhatsApp — DIFERIDA

**Estado:** aparcada. Motivo: WhatsApp (Kapso o Meta Cloud API) implica trámites y/o mensualidad. El
proyecto usa **solo Telegram** hasta que se publique. Gracias a la Task 10, retomarlo será añadir un
adaptador `whatsapp.py` + endpoint `/webhook/whatsapp`, sin tocar la lógica.

**Skills para cuando se retome:** `integrate-whatsapp`

### Checkpoint: Fase 3
- [ ] `pytest tests/ -q` verde
- [ ] Telegram sigue funcionando idéntico tras el refactor
- [ ] Añadir un canal nuevo es solo un archivo adaptador (verificado leyendo el código, sin implementarlo)
- [ ] Revisión con humano

---

## Fase 4: Descomposición de metas/proyectos

Progreso: [x] Task 12  ·  [ ] Task 13  ·  [ ] Task 14

### Task 12: Tabla `projects` + `ai_engine.decompose_goal()` — HECHA (2026-08-29)

**Description:** `projects` (user_id, team_id NULL, title, rubric TEXT, deadline DATE). `tasks.project_id`
NULL FK. `decompose_goal(goal, rubric, deadline) -> list[GeneratedTask]` llama a Gemini y reparte el
trabajo entre hoy y `deadline`.

**Acceptance criteria:**
- [x] Migración `0007_projects`: `projects` + `tasks.project_id`. `alembic check` limpio. Aplicada a Supabase (`0007_projects (head)`).
- [x] `GeneratedTask` (pydantic: title, due_date, note). `decompose_goal` valida cada item con pydantic, ordena por fecha y **clampa `due_date` a `[hoy, deadline]`**
- [x] Fallback si la IA falla o devuelve <3 tareas: `_fallback_plan` con 2-6 hitos repartidos por el rango
- [x] `src/flowtask/projects.py`: `create_project` (persiste la meta + una fila en `tasks` por tarea generada, `due_at` = due_date @ 09:00, `category=TASK`), `list_projects` (con progreso hechas/total)
- [x] Refactor menor: `AIEngine._call_gemini(prompt) -> dict` compartido (lanza en fallo)

**Verification:**
- [x] `pytest tests/test_decompose.py` → 6 passed (usa tareas de IA y ordena; clampa fechas fuera de rango; fallback si IA falla; fallback si IA devuelve pocas; `create_project` persiste; `list_projects` progreso)
- [x] `pytest -q` total: 44 passed, 2 skipped
- [ ] **TÚ (manual, tras Task 13):** meta real → plan coherente

**Dependencies:** Task 5, Task 7
**Files likely touched:** `src/flowtask/infrastructure/ai_engine.py`, `src/flowtask/infrastructure/database.py`, `src/flowtask/projects.py`, `migrations/versions/0007_projects.py`, `tests/test_decompose.py`
**Estimated scope:** Medium
**Skills:** `pytest`

---

### Task 13: Flujo de chat para crear un proyecto

**Description:** Comando `/proyecto` que abre una mini-conversación (meta → rúbrica → fecha límite) o
acepta todo en un mensaje. Al confirmar, llama a `decompose_goal`, persiste el `project` y sus tareas,
y devuelve el plan resumido. El usuario puede aceptar o pedir regenerar.

**Acceptance criteria:**
- [ ] Estado de conversación por `(platform, chat_id)` para las preguntas de seguimiento
- [ ] "Aceptar" persiste las tareas; "regenerar" vuelve a llamar a la IA sin duplicar
- [ ] Las tareas generadas entran en el barrido de recordatorios de Fase 2 automáticamente
- [ ] `/proyectos` lista los proyectos del usuario y su progreso (hechas / total)

**Verification:**
- [ ] Test `pytest`: máquina de estados del flujo (mensajes simulados en orden)
- [ ] Manual: crear un proyecto por chat, ver que llegan recordatorios los días siguientes

**Dependencies:** Task 12
**Files likely touched:** `src/flowtask/main.py`, `src/flowtask/projects.py`, `src/flowtask/convo_state.py`, `tests/test_project_flow.py`
**Estimated scope:** Medium

---

### Task 14: Reparto de tareas generadas entre el equipo

**Description:** Si el proyecto tiene `team_id`, al persistir las tareas se reparten entre los
`team_members` (round-robin, o por carga actual = nº de tareas pendientes). Cada asignado recibe un
mensaje con sus tareas.

**Acceptance criteria:**
- [ ] Proyecto de equipo → cada tarea generada tiene `assignee_id` de un miembro
- [ ] Reparto balancea por nº de tareas pendientes del miembro, no puro round-robin
- [ ] Cada miembro recibe una notificación con su parte
- [ ] `/proyectos` muestra el desglose por persona

**Verification:**
- [ ] Test `pytest`: proyecto de equipo con 3 miembros y 9 tareas → 3 cada uno
- [ ] Manual: crear proyecto de equipo, los 3 reciben su mensaje

**Dependencies:** Task 13
**Files likely touched:** `src/flowtask/projects.py`, `src/flowtask/teams.py`, `tests/test_distribution.py`
**Estimated scope:** Small

### Checkpoint: Fase 4
- [ ] `pytest tests/ -q` verde
- [ ] Una meta con rúbrica genera tareas diarias con fecha
- [ ] En un proyecto de equipo el trabajo queda repartido y notificado
- [ ] Revisión con humano

---

## Fase 5: App móvil (Expo / React Native)

### Task 15: Scaffold Expo + login Supabase Auth + vinculación de cuenta de chat

**Description:** App Expo nueva en `mobile/`. Login con Supabase Auth (email/OTP). Pantalla para
introducir el código de vinculación que el bot envía por chat, que asocia `auth.uid` a la fila `users`.
Endpoint API `POST /link` que valida el código.

**Acceptance criteria:**
- [ ] `mobile/` arranca en simulador iOS y emulador Android (workflow de la skill argent)
- [ ] Login con Supabase Auth funciona; sesión persiste entre reinicios
- [ ] `/vincular` en el bot genera un código de un solo uso con expiración
- [ ] Introducir el código en la app enlaza la cuenta; `users.auth_uid` queda seteado

**Verification:**
- [ ] Manual: login + vinculación end-to-end en un dispositivo
- [ ] Test `pytest` del endpoint `/link` (código válido / caducado / usado)

**Dependencies:** Task 4
**Files likely touched:** `mobile/` (proyecto nuevo), `src/flowtask/main.py`, `src/flowtask/auth_link.py`, `migrations/versions/0008_auth_uid.py`, `tests/test_link.py`
**Estimated scope:** Large
**Skills:** `argent-react-native-app-workflow`, `supabase-postgres-best-practices`

---

### Task 16: Pantalla "Hoy" — listar y completar tareas

**Description:** Endpoints REST `GET /api/tasks?date=` y `POST /api/tasks/{id}/complete` autenticados
con el JWT de Supabase (dependencia FastAPI que verifica el token y resuelve `user_id`). Pantalla que
lista las tareas del día agrupadas (MANGO / HÁBITOS / TAREAS) y permite marcarlas.

**Acceptance criteria:**
- [ ] Dependencia `get_current_user` que valida el JWT de Supabase y devuelve la fila `users`
- [ ] `GET /api/tasks` devuelve solo tareas del usuario autenticado, con `due_at`
- [ ] Completar en la app refleja en DB y desaparece de la lista
- [ ] Estados de carga / error / vacío en la pantalla

**Verification:**
- [ ] Test `pytest`: `GET /api/tasks` con JWT de A no devuelve tareas de B
- [ ] Manual: completar una tarea en la app, verla completada en el dashboard web

**Dependencies:** Task 15
**Files likely touched:** `src/flowtask/api.py`, `src/flowtask/main.py`, `mobile/src/screens/Today.tsx`, `mobile/src/api.ts`, `tests/test_api_tasks.py`
**Estimated scope:** Medium

---

### Task 17: Pantalla "Proyectos"

**Description:** `GET /api/projects` y `GET /api/projects/{id}` (con sus tareas y progreso). Pantalla
lista de proyectos + detalle con la línea de tiempo de tareas y, si es de equipo, el reparto por persona.

**Acceptance criteria:**
- [ ] Endpoints devuelven proyectos del usuario (propios + de sus equipos)
- [ ] Detalle muestra tareas ordenadas por `due_at` con estado
- [ ] Proyecto de equipo muestra el asignado de cada tarea
- [ ] Pull-to-refresh

**Verification:**
- [ ] Test `pytest` de los endpoints (aislamiento + forma del payload)
- [ ] Manual: crear proyecto por chat, verlo en la app con su progreso

**Dependencies:** Task 16, Task 13
**Files likely touched:** `src/flowtask/api.py`, `mobile/src/screens/Projects.tsx`, `mobile/src/screens/ProjectDetail.tsx`, `tests/test_api_projects.py`
**Estimated scope:** Medium

---

### Task 18: Push con `expo-notifications`

**Description:** Tabla `device_tokens` (user_id, expo_push_token, platform, updated_at). La app registra
su token al abrir. El barrido de recordatorios (Task 8), además del mensaje de chat, envía push a los
tokens del usuario vía la API de Expo Push.

**Acceptance criteria:**
- [ ] Migración `0009`: `device_tokens` único por token
- [ ] `POST /api/devices` guarda/renueva el token del usuario autenticado
- [ ] El sweep envía push a Expo además del mensaje de chat, sin duplicar si el envío de chat falla
- [ ] Tocar la push abre la tarea correspondiente (deep link)

**Verification:**
- [ ] Test `pytest`: sweep con un `device_token` registrado llama al cliente de Expo Push
- [ ] Manual: tarea "test 2 min", llega push al dispositivo y abre la tarea

**Dependencies:** Task 16, Task 8
**Files likely touched:** `src/flowtask/scheduler.py`, `src/flowtask/api.py`, `src/flowtask/push.py`, `mobile/src/push.ts`, `migrations/versions/0009_device_tokens.py`, `tests/test_push.py`
**Estimated scope:** Medium
**Skills:** `capacitor-push-notifications` (solo como referencia FCM; el envío real es Expo Push)

### Checkpoint: Fase 5
- [ ] `pytest tests/ -q` verde
- [ ] App: login, vinculación, listar/completar tareas y ver proyectos
- [ ] Recordatorio llega como push al móvil
- [ ] Revisión con humano

---

## Fase 6: Deploy y calidad

### Task 19: Deploy en Railway (web + scheduler)

**Description:** `Procfile` / config de Railway para el proceso web con el scheduler embebido. Todas las
env vars cargadas. Pooler de Supabase (6543). Healthcheck. `alembic upgrade head` en el release.

**Acceptance criteria:**
- [ ] Deploy en Railway sirve el webhook con HTTPS y URL estable
- [ ] Webhook de Telegram apuntando a la URL de Railway
- [ ] `alembic upgrade head` corre en cada release (release command / pre-deploy)
- [ ] Una sola réplica; documentado el paso a worker aparte si se escala
- [ ] Healthcheck `/health` que verifica DB y scheduler vivo

**Verification:**
- [ ] Manual: mensaje real por Telegram contra producción, con recordatorio a la hora fijada
- [ ] Logs de Railway sin errores de conexión a Supabase

**Dependencies:** Task 18
**Files likely touched:** `Procfile`, `railway.json`/`railway.toml`, `src/flowtask/main.py`, `README.md`
**Estimated scope:** Small
**Skills:** `use-railway`

---

### Task 20: Suite `pytest` + reescritura del `ci.yml`

**Description:** Consolidar los tests de todas las fases bajo `tests/` con `pytest` + `pytest-asyncio`.
`conftest.py` con una DB Postgres de test (contenedor o schema efímero) y fixtures de usuario/equipo.
Reescribir `.github/workflows/ci.yml` para: `ruff check`, `alembic upgrade head` contra DB de test,
`pytest --cov`.

**Acceptance criteria:**
- [ ] `pytest tests/ -q` corre toda la suite en local y en CI
- [ ] `ci.yml` sin referencias a `backend/src`, `black`, `flake8`, `isort`, gitleaks inexistente
- [ ] CI verde en un PR de prueba
- [ ] Cobertura reportada (sin umbral que rompa el build al principio)

**Verification:**
- [ ] PR de prueba → checks de CI en verde
- [ ] `ruff check .` limpio

**Dependencies:** Task 19
**Files likely touched:** `.github/workflows/ci.yml`, `tests/conftest.py`, `pyproject.toml`, `tests/**`
**Estimated scope:** Medium
**Skills:** `pytest`

### Checkpoint: Fase 6 (Completo)
- [ ] Todos los criterios de aceptación cumplidos
- [ ] CI verde, desplegado en Railway, datos en Supabase
- [ ] Telegram + WhatsApp + app móvil operativos con recordatorios y proyectos
- [ ] Revisión final con humano

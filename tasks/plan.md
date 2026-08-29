# Implementation Plan: FlowTask — secretaria IA multiusuario

## Overview

FlowTask hoy: FastAPI con un webhook de Telegram, `ai_engine.py` (Gemini 1.5 Flash + reglas de
keywords) que clasifica mensajes en `MANGO_REL` / `HABIT` / `TASK`, `database.py` con SQLite y un
`TaskModel` **sin `user_id`** (mono-usuario de facto), dashboard Jinja2 y un `cli_manager.py`.

El objetivo es convertirlo en un asistente real: Postgres multiusuario con equipos, recordatorios a
la hora de cada tarea, fechas en lenguaje natural, entrada por WhatsApp además de Telegram,
descomposición de metas/proyectos en tareas diarias, y una app móvil React Native. Deploy en Railway,
datos en Supabase.

El trabajo se corta en **rebanadas verticales**: cada fase deja el bot funcionando end-to-end.

## Architecture Decisions

- **Se mantiene SQLAlchemy**, no se reescribe la capa de datos. Migración a Postgres = cambiar la URL
  de conexión + driver `psycopg` + añadir Alembic. `TaskModel` sigue siendo la fuente de verdad del
  esquema; Supabase declarative-schema/RLS se añade encima como defensa en profundidad.
- **La app móvil habla con la API de FlowTask, no directamente con Supabase.** Un solo camino de auth
  y de lógica. RLS de Supabase queda como segunda barrera, el filtrado por `user_id` en cada query es
  la barrera primaria. El backend conecta con el *transaction pooler* de Supabase (puerto 6543).
- **Identidad = cuenta de chat.** `users` se crea/upsertea al primer mensaje desde un `(platform, chat_id)`.
  La app móvil usa Supabase Auth y enlaza su `auth.uid` a esa fila `users` con un código de vinculación
  enviado por el bot. No se construye login propio.
- **Hosting: máquina propia siempre encendida** (decidido 2026-08-29), no Railway. Un solo proceso
  `uvicorn` levanta: bot de Telegram (long-polling, `TELEGRAM_POLLING=1`, sin URL pública) +
  `AsyncIOScheduler` + panel web local. Datos en Supabase para persistir entre reinicios.
  Sin jobstore persistente de APScheduler: el único job se re-registra en cada arranque.
  Una sola instancia; si algún día hay varias, `pg_advisory_lock` alrededor del barrido.
- **Recordatorios por barrido, no un job por tarea.** Un job cada 60 s:
  `SELECT ... WHERE due_at <= now() AND reminder_sent = false`. Menos estado, menos jobs huérfanos.
- **Solo Telegram por ahora** (gratis, sin trámites ni mensualidades). Aun así se hace el refactor a un
  núcleo agnóstico de plataforma: `handle_incoming_message(platform, chat_id, text)` + dispatcher
  `send_message(platform, ...)`. Telegram es el único adaptador hoy; añadir WhatsApp u otro canal
  después será solo un adaptador nuevo, sin tocar la lógica. WhatsApp/Kapso queda **diferido** hasta
  que el proyecto se publique.
- **Descomposición de metas** = una llamada nueva a Gemini `decompose_goal(goal, rubric, deadline)` que
  devuelve una lista de tareas con `due_at`. Se persisten como `tasks` normales ligadas por `project_id`.
- **App móvil: Expo (React Native)** con `expo-notifications` para push. La skill
  `capacitor-push-notifications` **no aplica** a Expo (ver Open Questions).

## Task List

Tareas y checkpoints en `tasks/todo.md`. Orden = orden de implementación.

### Fase 0: Fundaciones
- Task 1: Limpieza del repo y saneo de dependencias
- Task 2: Provisionar Supabase + Railway y centralizar configuración

### Fase 1: Postgres multiusuario + equipos (objetivo 1)
- Task 3: Migrar SQLAlchemy de SQLite a Supabase Postgres + Alembic
- Task 4: Multiusuario — tabla `users`, `tasks.user_id`, aislamiento en todas las queries
- Task 5: Equipos — `teams`, `team_members`, `tasks.team_id`, `tasks.assignee_id`
- Task 6: Políticas RLS en Supabase + tests de aislamiento

### Fase 2: Fechas naturales + recordatorios (objetivos 2 y 3)
- Task 7: Parser de fecha/hora en español (`dateparser`) + columnas `due_at` / `reminder_sent`
- Task 8: `AsyncIOScheduler` con jobstore en Postgres + barrido de recordatorios cada 60 s
- Task 9: Hábitos recurrentes se regeneran a diario; `/list` y dashboard muestran la hora

### Fase 3: Preparar multi-canal, sin coste (objetivo 4, parcial)
- Task 10: Refactor a núcleo agnóstico de plataforma (`handle_incoming_message` / `send_message`)
- Task 11: **DIFERIDA** — Integración WhatsApp vía Kapso. Se retoma solo si el proyecto se publica y se
  acepta la mensualidad (o se migra a WhatsApp Cloud API de Meta directo).

### Fase 4: Descomposición de metas/proyectos (objetivo 5)
- Task 12: Tabla `projects` + `tasks.project_id` + `ai_engine.decompose_goal()`
- Task 13: Flujo de chat para crear un proyecto (meta + rúbrica + fecha límite → tareas diarias)
- Task 14: Reparto de las tareas generadas entre los miembros del equipo

### Fase 5: App móvil (objetivo 6)
- Task 15: Scaffold Expo + login con Supabase Auth + vinculación de cuenta de chat
- Task 16: Pantalla "Hoy" — listar y completar tareas contra la API
- Task 17: Pantalla "Proyectos"
- Task 18: Push con `expo-notifications` — tabla `device_tokens`, el scheduler también hace push

### Fase 6: Deploy y calidad
- Task 19: Deploy en Railway (web + scheduler, env vars, pooler de Supabase)
- Task 20: Suite `pytest` + reescritura del `ci.yml` roto

### Checkpoints
- Tras Fase 1 (Task 6): aislamiento multiusuario verificado
- Tras Fase 2 (Task 9): recordatorio real llega al chat a la hora fijada
- Tras Fase 3 (Task 10): Telegram sigue igual tras el refactor; añadir un canal es solo un adaptador
- Tras Fase 4 (Task 14): una meta genera tareas diarias con fecha, repartidas al equipo
- Tras Fase 5 (Task 18): app móvil lista y completa tareas y recibe push
- Tras Fase 6 (Task 20): CI verde, desplegado, revisión con humano

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| APScheduler en el proceso web → doble envío con >1 réplica o en reinicios | Alto | Jobstore en Postgres + 1 réplica; `pg_advisory_lock` en el barrido antes de escalar |
| Límite de conexiones de Supabase con el pool de SQLAlchemy | Alto | Transaction pooler (6543), `pool_size` bajo, `pool_pre_ping=True` |
| `capacitor-push-notifications` no sirve para Expo | Medio | Usar `expo-notifications`; o construir la app con Capacitor en vez de RN (Open Question) |
| Gemini 1.5 Flash en retirada / cambio de nombre de modelo | Medio | Aislar el nombre del modelo en config; probar `gemini-2.0-flash` |
| `dateparser` en español: ambigüedad "el jueves", "en 3 días" | Medio | `PREFER_DATES_FROM=future`, `languages=['es']`, confirmar la fecha interpretada en la respuesta del bot |
| Hosting = máquina propia encendida (decidido). Si se apaga, los recordatorios no salen esa ventana; el barrido recupera lo atrasado al volver | Bajo | Dejar la máquina encendida; el barrido de 60 s recupera lo vencido tras un corte |
| Migrar datos SQLite existentes | Bajo | Es una demo; empezar Postgres limpio, script de import opcional |
| `TaskModel` sin `user_id` hoy → toda query actual asume 1 usuario | Alto | Task 4 toca todas las queries de `main.py`; sin ella el resto de fases arrastran el bug |

## Decisiones tomadas (2026-08-28)

- **App móvil: Expo (React Native)**, push con `expo-notifications`.
- **Canal: solo Telegram** por ahora (gratis, sin trámites). WhatsApp diferido.
- **La app móvil pega a la API de FlowTask**, no a Supabase directo.

## Decisiones tomadas (2026-08-29)

- **Hosting: máquina propia siempre encendida** (no Railway). Bot por long-polling (`TELEGRAM_POLLING=1`),
  sin URL pública. `run.bat` + carpeta de Inicio de Windows.
- **Reorden: la Task 19 (deploy) se hace antes de la Fase 5**, para verificar Fases 1-4 con Telegram real
  y darle a la app móvil una API contra la que trabajar.

## Open Questions

- **¿Login propio o identidad de chat + Supabase Auth?** El plan asume identidad de chat con
  vinculación por código de un solo uso.

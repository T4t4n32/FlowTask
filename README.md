FlowTask - Documentación Fundacional del Proyecto
Estado del Documento: 🚧 En Revisión | Versión 0.2
Última Actualización: [Fecha]
Propósito: Define la misión, visión, alcance, arquitectura y planes de un MVP para FlowTask, un asistente de calendario conversacional.

📋 Índice
Resumen Ejecutivo

Definición Estratégica

Decisión Crítica: Canal de Mensajería

Definición del MVP

Arquitectura Técnica Propuesta

Plan de Trabajo & Roadmap

Presupuesto y Costos

Riesgos y Mitigaciones

Apéndices

🎯 1. Resumen Ejecutivo
FlowTask es un asistente de productividad que permite gestionar un calendario personal mediante mensajes de texto en lenguaje natural. Su objetivo es reducir el tiempo y esfuerzo de registro de eventos de varios minutos a menos de 10 segundos.

Problema: Los calendarios tradicionales requieren una entrada manual llena de fricciones (abrir app, hacer clic, rellenar campos).

Solución: Un asistente conversacional accesible principalmente a través de un canal de mensajería familiar (por definir), que interpreta frases coloquiales como "Reunión con Juan mañana a las 3pm".

MVP Core: Backend que recibe un mensaje → Procesa lenguaje natural (NLP) → Extrae datos del evento → Lo guarda en un calendario → Confirma al usuario.

Público Objetivo: Adultos ocupados (25-55 años) que usan mensajería instantánea a diario y buscan optimizar tareas administrativas.

🧭 2. Definición Estratégica
Misión
Reducir la fricción cognitiva y temporal en la gestión de agendas personales y profesionales, permitiendo a las personas registrar y organizar sus compromisos en segundos, a través de conversaciones naturales.

Visión
Convertirse en la capa de inteligencia conversacional predilecta para la gestión del tiempo personal.

Propuesta de Valor Única (UVP)
"Tu calendario, conversacional. Agenda eventos y tareas simplemente enviando un mensaje de texto, como si se lo contaras a un amigo."

⚠️ DECISIÓN CRÍTICA: Canal de Mensajería
Este es el punto de decisión más importante del proyecto. Basado en el análisis de riesgos (políticas y costos actualizados de la API de WhatsApp), se deben evaluar las siguientes opciones:

Opción	Descripción	Pros	Contras	Estado
Opción A: WhatsApp vía BSP	Usar un socio oficial (BSP) como Wati, MessageBird o 360dialog.	Menor riesgo regulatorio, herramientas listas para usar (inbox, plantillas).	Costo mensual base (~$49-99) + costo por mensaje enviado. Uso en área gris (C2B2C).	PENDIENTE
[Contactar a BSP para validar]
Opción B: Telegram Bot	Desarrollar un bot utilizando la API oficial de Bots de Telegram.	Costo ~$0, políticas flexibles, desarrollo rápido y sencillo, gran capacidad para interactividad (botones, comandos).	Menor penetración que WhatsApp en algunos mercados (depende de la audiencia objetivo).	RECOMENDADA para MVP
Opción C: Email (Canal Inicial)	Usar el correo electrónico como canal de entrada principal (ej: enviar a plan@flowtask.com).	Universal, costo cero, sin restricciones de plataforma, ideal para validar el núcleo de NLP.	Menos inmediato que la mensajería instantánea, UX menos atractiva.	Viable para prototipo
📌 Decisión y Justificación:
[Elegir una opción aquí tras la investigación. Ej: "Se elige la Opción B (Telegram Bot) para el MVP por su costo cero, flexibilidad de desarrollo y menor riesgo, permitiendo validar el núcleo de producto en 3 meses con el presupuesto disponible."]

🎨 3. Definición del MVP
Alcance (Qué SÍ está incluido - V1)
Backend Core: API en Python/Node.js que reciba webhooks del canal de mensajería elegido.

Procesador de Lenguaje Natural (NLP): Capacidad para entender:

Eventos únicos con fecha/hora ("Reunión mañana a las 3pm").

Repeticiones semanales simples ("Yoga todos los martes").

Gestor de Calendarios: Almacenamiento básico en Firebase Firestore (o similar).

Flujo de Confirmación: Respuesta automática al usuario confirmando el evento creado o pidiendo aclaración.

Interfaz Web Básica: Un dashboard mínimo (localhost:3000) para ver eventos registrados (para depuración y demo).

Alcance (Qué NO está incluido - V1)
Aplicación móvil nativa (Flutter/React Native).

Sincronización bidireccional con Google/Apple Calendar.

Gestión de equipos o calendarios compartidos.

Sistema de notificaciones push complejo.

Panel de administración de usuarios.

⚙️ 4. Arquitectura Técnica Propuesta
Diagrama de Flujo de Alto Nivel
text
Usuario envía mensaje -> [Canal: Telegram/WhatsApp/Email]
                              ⬇
          Webhook -> [Backend API (Python + Flask/FastAPI)]
                              ⬇
               [Procesador NLP (Chrono + Lógica Personalizada)]
                              ⬇
        [Gestor de Calendario (Firebase Firestore / Simple JSON)]
                              ⬇
         [Generador de Respuesta] -> Envía confirmación al usuario
Stack Tecnológico Recomendado (Basado en Opción B - Telegram)
Backend: Python con FastAPI (simple y rápido) o Flask.

Alojamiento: Railway.app o Render.com (plan gratis, despliegue fácil con Git).

Base de Datos: Firebase Firestore (por su modelo flexible y capa gratuita) o Supabase (PostgreSQL gratuito).

NLP: Librería chrono-node (para fechas) + lógica personalizada en regex/string para repeticiones.

Canal: API Oficial de Bots de Telegram (via python-telegram-bot).

Estructura de Carpetas del Proyecto
bash
flowtask-mvp/
├── backend/
│   ├── app/                 # Código principal de la API
│   │   ├── api/             # Endpoints y webhooks
│   │   ├── core/            # Configuración, seguridad
│   │   ├── models/          # Modelos de datos Pydantic/SQL
│   │   ├── nlp/             # Lógica de procesamiento de lenguaje
│   │   │   └── parser.py    # (Ej: con Chrono y regex)
│   │   ├── services/        # Lógica de negocio (calendario, respuestas)
│   │   └── utils/           # Funciones auxiliares
│   ├── tests/               # Pruebas
│   ├── requirements.txt
│   └── main.py              # Punto de entrada
├── docs/                    # Documentación adicional
├── scripts/                 # Scripts de despliegue o DB
└── README.md                # Este archivo
🗺️ 5. Plan de Trabajo & Roadmap
Fase 1: Semanas 1-3 - Cimientos y Prototipo Conversacional
Decidir y configurar el canal de mensajería (Telegram Bot/Email).

Configurar entorno de desarrollo y repositorio.

Implementar backend básico (FastAPI) que reciba un webhook y loguee el mensaje.

Implementar lógica central de NLP para fechas únicas y repeticiones semanales.

Conectar con Firebase Firestore y guardar un evento de prueba.

Hito: Poder enviar "Prueba mañana a las 5" y ver el evento guardado en Firestore.

Fase 2: Semanas 4-6 - Flujo Completo y Validación
Implementar flujo completo: Mensaje → Procesamiento → Guardado → Confirmación al usuario.

Mejorar el parser de NLP con más variantes de lenguaje.

Crear dashboard web básico (localhost:3000) para ver eventos.

Realizar pruebas con 5-10 usuarios beta (amigos, familia).

Hito: Tener un flujo de usuario completo funcional con 5 usuarios reales.

Fase 3: Semanas 7-12 - Robustez y Preparación para Lanzamiento
Implementar manejo elegante de errores (¿qué pasa si la IA no entiende?).

Añadir comandos básicos (/ayuda, /hoy, /borrar).

Configurar despliegue en producción (Railway/Render).

Crear página de landing simple y política de privacidad.

Hito: MVP estable desplegado, listo para compartir en foros (Product Hunt, Reddit).

💰 6. Presupuesto y Costos (Estimación para 3 meses)
Basado en un stack de bajo costo (ej: Telegram + Railway + Firebase).

Recurso	Proveedor	Costo Mensual Estimado	Notas
Alojamiento Backend	Railway.app / Render.com	$0 - $5	Plan gratuito suficiente para inicio.
Base de Datos	Firebase Firestore	$0	Límite generoso gratuito.
Canal de Mensajería	Telegram Bot API	$0	Sin costo por mensajes o API.
Dominio	Cloudflare / Epik	~$10 / año	Opcional para landing page.
Costos Imprevistos	-	$50	Buffer para servicios premium.
TOTAL ESTIMADO (3 meses)		< $100 USD	Muy por debajo del presupuesto de $500.
🚨 7. Riesgos y Mitigaciones
Riesgo	Impacto	Probabilidad	Mitigación
1. Políticas de Plataforma (si se usa WhatsApp)	Alto (Bloqueo total)	Media-Alta	ELEGIR TELEGRAM/EMAIL. Si se insiste en WhatsApp, usar BSP oficial y consultar previamente.
2. NLP no entiende al usuario	Alto (Abandono)	Media	Invertir en fase de prototipo y testing. Tener un flujo de error claro ("No entendí, ¿podrías decirlo de otra forma?").
3. Costos se escalan	Medio	Baja	Usar stack gratuito (Telegram, Firebase plan Spark). Monitorear métricas de uso.
4. Poco Engagement	Medio	Media	Validar con MVP conversacional antes de desarrollar app móvil. Buscar "ganchos" virales (compartir eventos fácil).
📎 Apéndices
A. Comandos Útiles para Iniciar
bash
# 1. Crear entorno y repositorio
mkdir flowtask-mvp && cd flowtask-mvp
git init
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 2. Instalar dependencias iniciales (ejemplo para FastAPI + Telegram)
pip install fastapi uvicorn python-telegram-bot firebase-admin chrono
pip freeze > requirements.txt

# 3. Estructura inicial de carpetas (crear las carpetas listadas arriba)
mkdir -p backend/app/{api,core,models,nlp,services,utils} backend/tests docs scripts
B. Enlaces y Recursos Clave
Documentación de Bots de Telegram

FastAPI - Tutorial rápido

Firebase Firestore - Primeros pasos

Chrono (biblioteca para parseo de fechas naturales)

C. Próximos Pasos Inmediatos
Tomar la Decisión del Canal: Basado en este documento, elegir entre Telegram (recomendado), Email o WhatsApp vía BSP.

Crear el Repositorio: Crear un repo en GitHub/GitLab y copiar este README.md como base.

Configurar las Cuentas de Servicio: Crear cuentas en:

Telegram (para crear el bot).

Firebase (para la base de datos).

Railway (para el despliegue).

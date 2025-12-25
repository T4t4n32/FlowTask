# FlowTask - Documentación Fundacional del Proyecto

## Resumen del Proyecto

**FlowTask** es un asistente de productividad que convierte mensajes de texto en lenguaje natural en eventos de calendario estructurados. El producto aborda la fricción asociada con la entrada manual en aplicaciones de calendario tradicionales.

### Visión
Ser la interfaz conversacional de referencia para la gestión de tiempo personal.

### Problema Central
- La entrada manual en calendarios requiere múltiples pasos y cambios de contexto
- El proceso consume entre 1 y 5 minutos por evento
- Existe una alta probabilidad de error al especificar fechas, horas y patrones de recurrencia

### Solución Propuesta
Un sistema que interpreta frases conversacionales del usuario (como "Reunión con el equipo mañana a las 3pm") y las convierte automáticamente en eventos de calendario con confirmación contextual.

### Público Objetivo Principal
Profesionales entre 25 y 55 años que gestionan agendas ocupadas y buscan optimizar tareas administrativas recurrentes.

## Estado del Proyecto

**Fase actual**: Diseño y planificación previa al desarrollo  
**Versión del documento**: 1.0  
**Última revisión**: FECHA  
**Próximo hito**: Decisión final sobre canal de mensajería y creación del repositorio

## Decisiones Arquitectónicas Clave

### 1. Canal de Mensajería (Por Definir)

Se están evaluando las siguientes opciones:

**Opción A: Telegram Bot API**
- Ventajas: Costo cero, políticas flexibles, documentación completa, soporte para interactividad
- Desventajas: Menor penetración que WhatsApp en algunos mercados
- Recomendación inicial: Opción preferente para MVP

**Opción B: WhatsApp vía Business Solution Provider (BSP)**
- Ventajas: Alta penetración en mercados objetivo, familiaridad del usuario
- Desventajas: Costos por mensaje, políticas restrictivas, riesgo de suspensión
- Estado: Requiere consulta con proveedores oficiales

**Opción C: Correo electrónico**
- Ventajas: Universal, sin restricciones de plataforma
- Desventajas: Experiencia de usuario menos inmediata
- Estado: Opción de respaldo para validación inicial

### 2. Stack Tecnológico Propuesto

**Backend**
- Lenguaje: Python 3.11+
- Framework: FastAPI (para APIs rápidas y documentación automática)
- Alojamiento: Railway.app o Render.com (planes gratuitos iniciales)
- Base de datos: Firebase Firestore (modelo flexible, capa gratuita)

**Procesamiento de Lenguaje Natural**
- Bibliotecas principales: spaCy (para español), dateparser, chrono-es
- Enfoque: Combinación de reglas específicas y modelos de lenguaje

**Infraestructura**
- Control de versiones: Git con GitHub/GitLab
- CI/CD: GitHub Actions
- Monitoreo: Logtail (logs), Healthchecks (monitoreo de endpoints)

## Alcance del MVP

### Funcionalidades Incluidas (Fase 1)
1. Recepción y procesamiento de mensajes a través del canal seleccionado
2. Interpretación de eventos únicos con fecha y hora específica
3. Detección de patrones de recurrencia semanal simple
4. Confirmación contextual al usuario antes de crear el evento
5. Almacenamiento básico en base de datos
6. Panel web mínimo para visualización de eventos (propósito de depuración)

### Funcionalidades Excluidas (Fase 1)
1. Aplicación móvil nativa
2. Sincronización con calendarios externos (Google, Apple, Outlook)
3. Gestión de equipos o calendarios compartidos
4. Sistema avanzado de recordatorios
5. Panel de administración completo

## Plan de Trabajo

### Fase 1: Configuración y Núcleo (Semanas 1-4)
- Decisión final sobre canal de mensajería
- Configuración del repositorio y entorno de desarrollo
- Implementación del backend básico con endpoint de webhook
- Desarrollo del procesador de lenguaje natural para casos básicos
- Integración con base de datos

### Fase 2: Flujo Completo y Validación (Semanas 5-8)
- Implementación del flujo completo: mensaje → procesamiento → almacenamiento → confirmación
- Desarrollo del panel web básico para visualización
- Pruebas con usuarios beta (5-10 personas)
- Refinamiento basado en feedback

### Fase 3: Robustez y Preparación para Lanzamiento (Semanas 9-12)
- Implementación de manejo de errores y casos límite
- Adición de comandos básicos (/ayuda, /hoy, /eventos)
- Configuración de despliegue en producción
- Documentación para usuarios finales
- Lanzamiento controlado a comunidad inicial

## Estructura del Repositorio

```
flowtask/
├── .github/                  # Configuración de GitHub
│   └── workflows/           # Pipelines de CI/CD
├── backend/                  # Código del servidor
│   ├── src/                 # Código fuente
│   │   ├── api/            # Endpoints y controladores
│   │   ├── core/           # Configuración y utilidades
│   │   ├── domain/         # Lógica de negocio
│   │   └── infrastructure/ # Conexiones externas
│   ├── tests/              # Pruebas automatizadas
│   └── requirements/       # Dependencias
├── docs/                    # Documentación
│   ├── architecture/       # Decisiones arquitectónicas
│   ├── api/               # Documentación de API
│   └── user/              # Guías de usuario
├── scripts/                # Scripts de utilidad
└── README.md               # Este documento
```

## Gestión del Proyecto

### Metodología
- Enfoque iterativo basado en sprints de 2 semanas
- Priorización basada en valor de usuario y riesgo técnico
- Revisión semanal de progreso y ajuste de planificación

### Control de Versiones
- Rama principal (main): código de producción
- Rama de desarrollo (develop): integración continua
- Ramas de características (feature/*): desarrollo de funcionalidades específicas
- Ramas de corrección (hotfix/*): soluciones urgentes

### Criterios de Aceptación
Para considerar completada una funcionalidad:
1. Código implementado y probado
2. Documentación actualizada
3. Revisión de código aprobada por al menos una persona
4. Pruebas automatizadas con cobertura adecuada
5. Desplegado en entorno de prueba y verificado

## Presupuesto y Recursos

### Presupuesto Inicial
- Total disponible: 500 USD
- Período cubierto: 3 meses

### Estimación de Costos Mensuales
- Alojamiento backend: 0-5 USD (plan gratuito o básico)
- Base de datos: 0 USD (Firebase free tier)
- Canal de mensajería: 0 USD (Telegram) o 50+ USD (WhatsApp vía BSP)
- Dominio y DNS: 10 USD/año (opcional inicialmente)
- Buffer para imprevistos: 50 USD

### Requisitos de Personal
- 1 desarrollador full-stack (emprendedor solitario)
- Tiempo estimado: 20 horas/semana
- Habilidades requeridas: Python, APIs, procesamiento de lenguaje natural, gestión de proyectos

## Evaluación de Riesgos

### Riesgos Técnicos
1. **Precisión del procesamiento de lenguaje natural**
   - Impacto: Alto. Si el sistema no entiende correctamente, los usuarios abandonarán.
   - Mitigación: Comenzar con patrones simples, implementar confirmación contextual, plan de mejora iterativa.

2. **Fiabilidad del canal de mensajería**
   - Impacto: Alto. Interrupciones impedirían el uso del producto.
   - Mitigación: Seleccionar proveedor estable, implementar sistema de reintentos, monitoreo proactivo.

### Riesgos de Negocio
1. **Adopción limitada por el canal seleccionado**
   - Impacto: Medio. Si los usuarios objetivo no usan el canal elegido, no adoptarán el producto.
   - Mitigación: Investigar hábitos del público objetivo, considerar multi-canal en el futuro.

2. **Competencia de soluciones establecidas**
   - Impacto: Medio. Calendarios tradicionales tienen ventaja de integración.
   - Mitigación: Enfocarse en ventaja diferencial (velocidad, experiencia conversacional).

### Riesgos Operacionales
1. **Escalabilidad de costos**
   - Impacto: Medio. Crecimiento podría hacer insostenible el modelo actual.
   - Mitigación: Monitoreo constante de métricas de costo por usuario, plan de monetización temprano.

## Métricas de Éxito

### Métricas de Producto (MVP)
1. **Precisión de interpretación**: >85% de mensajes interpretados correctamente sin intervención manual
2. **Tiempo de registro**: Reducción a menos de 10 segundos desde mensaje a evento creado
3. **Tasa de retención**: >40% de usuarios activos semanales después de 4 semanas

### Métricas Técnicas
1. **Tiempo de respuesta**: <2 segundos para procesamiento y respuesta
2. **Disponibilidad**: >99% de tiempo operativo
3. **Cobertura de pruebas**: >80% del código base

### Métricas de Negocio (Post-MVP)
1. **Conversión a premium**: >5% de usuarios activos
2. **Costo de adquisición**: <3 USD por usuario
3. **Satisfacción del usuario**: NPS >30

## Próximos Pasos Inmediatos

1. **Decisión final sobre canal de mensajería** (Día 1-3)
   - Investigar hábitos del público objetivo
   - Contactar proveedores de WhatsApp BSP para consulta
   - Tomar decisión documentada

2. **Configuración del repositorio** (Día 4)
   - Crear repositorio en GitHub/GitLab
   - Establecer estructura inicial de carpetas
   - Configurar herramientas básicas (linting, formateo)

3. **Configuración de cuentas de servicio** (Día 5)
   - Crear bot de Telegram (si es la opción seleccionada)
   - Configurar proyecto en Firebase
   - Crear cuenta en Railway/Render

4. **Desarrollo del núcleo de procesamiento** (Día 6-15)
   - Implementar parser de fechas y horas en español
   - Desarrollar detector de patrones de recurrencia
   - Crear pruebas unitarias para casos de uso básicos

## Documentación Relacionada

- [Análisis de viabilidad inicial] - Evaluación técnica y de mercado
- [Decisiones arquitectónicas] - Detalle de opciones consideradas y justificación
- [Plan de pruebas] - Estrategia y casos de prueba
- [Política de privacidad] - Tratamiento de datos de usuario

## Contacto y Soporte

- **Responsable del proyecto**: [Nombre del emprendedor]
- **Método de contacto principal**: [Correo electrónico]
- **Repositorio de código**: [URL por definir]
- **Seguimiento de issues**: Sistema de issues del repositorio

---

*Este documento es un artefacto vivo que se actualizará a lo largo del proyecto. Los cambios significativos se registrarán en el historial de versiones.*

**Historial de versiones**:
- 1.0 (FECHA): Versión inicial para inicio del proyecto

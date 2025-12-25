"""
Punto de entrada principal de la aplicación FlowTask.
"""
import os
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de variables de entorno
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN no está configurado en las variables de entorno")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Maneja eventos de inicio y cierre de la aplicación.
    Context manager para inicializar y limpiar recursos.
    """
    # ===== INICIALIZACIÓN =====
    logger.info("🚀 Iniciando FlowTask API...")
    
    # Inicializar Firebase
    try:
        from infrastructure.firebase_client import get_firestore_client
        db = get_firestore_client()
        logger.info("✅ Firebase Firestore inicializado correctamente")
        
        # Prueba de conexión
        test_doc = db.collection("system_status").document("startup")
        test_doc.set({
            "status": "starting",
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        
    except Exception as e:
        logger.error(f"⚠️ Error inicializando Firebase: {e}")
        # No detenemos la app, pero registramos el error
    
    logger.info("✅ FlowTask API lista para recibir peticiones")
    
    yield  # La aplicación corre aquí
    
    # ===== LIMPIEZA =====
    logger.info("👋 Cerrando FlowTask API...")
    # Aquí iría la limpieza de recursos si fuera necesario

# Crear la aplicación FastAPI
app = FastAPI(
    title="FlowTask API",
    description="API para el asistente de calendario conversacional",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.get("/")
async def root():
    """Endpoint de verificación de salud."""
    return {
        "status": "active",
        "service": "FlowTask API",
        "version": "0.1.0",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }

@app.get("/health")
async def health_check():
    """Endpoint para verificar el estado del servicio."""
    from infrastructure.firebase_client import test_connection
    
    # Verificar Firebase
    firebase_ok, firebase_msg = test_connection()
    
    # Verificar Telegram (conexión básica)
    telegram_ok = bool(TELEGRAM_TOKEN)
    
    status = "healthy" if firebase_ok and telegram_ok else "degraded"
    
    return {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "services": {
            "firebase": {
                "status": "connected" if firebase_ok else "disconnected",
                "message": firebase_msg
            },
            "telegram": {
                "status": "configured" if telegram_ok else "not_configured",
                "bot_name": "FlowTaskCalendarbot" if telegram_ok else None
            }
        }
    }

@app.get("/api/v1/status")
async def api_status():
    """Endpoint extendido de estado para monitoreo."""
    import datetime
    from infrastructure.firebase_client import get_firestore_client
    
    db = get_firestore_client()
    
    return {
        "service": "FlowTask",
        "environment": "development",
        "uptime": "0:00:00",  # Podríamos calcularlo si agregamos métricas
        "timestamp": datetime.datetime.now().isoformat(),
        "database": {
            "type": "Firebase Firestore",
            "status": "connected"
        }
    }

# Solo para ejecución directa
if __name__ == "__main__":
    import uvicorn
    import sys
    
    # Permite ejecutar con: python main.py
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if "reload" in sys.argv else False
    )

"""
Versión simplificada de FlowTask API.
"""
import os
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan simplificado sin Firebase temporalmente."""
    logger.info("🚀 Iniciando FlowTask API (modo simplificado)...")
    yield
    logger.info("👋 Cerrando FlowTask API...")

# Crear la aplicación FastAPI
app = FastAPI(
    title="FlowTask API",
    description="API para el asistente de calendario conversacional",
    version="0.1.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {
        "status": "active",
        "service": "FlowTask API",
        "version": "0.1.0",
        "mode": "simplified"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "firebase": "not_initialized",
        "telegram": "configured" if os.getenv("TELEGRAM_BOT_TOKEN") else "not_configured"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main_simple:app", host="0.0.0.0", port=8000, reload=True)

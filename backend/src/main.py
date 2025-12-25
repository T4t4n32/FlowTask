"""
Punto de entrada principal de la aplicación FlowTask.
"""

import os
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Configuración de variables de entorno
TELEGRAM_TOKEN = os.getenv("8535132071:AAE1Iywb8mdorcjzPS8X60OR0tZC8EuAeHk")
FIREBASE_CREDENTIALS_PATH = os.getenv(
    "FIREBASE_CREDENTIALS_PATH", "../secure_credentials/firebase-creds.json"
)

if not TELEGRAM_TOKEN:
    raise ValueError(
        "TELEGRAM_BOT_TOKEN no está configurado en las variables de entorno"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja eventos de inicio y cierre de la aplicación."""
    # Inicializar conexiones aquí (Firebase, etc.)
    print("🚀 Iniciando FlowTask...")
    yield
    # Cerrar conexiones aquí
    print("👋 Cerrando FlowTask...")


# Crear la aplicación FastAPI
app = FastAPI(
    title="FlowTask API",
    description="API para el asistente de calendario conversacional",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Endpoint de verificación de salud."""
    return {"status": "active", "service": "FlowTask API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    """Endpoint para verificar el estado del servicio."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

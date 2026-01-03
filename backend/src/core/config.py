"""
Configuración central de FlowTask.
"""
import os
from pathlib import Path
from typing import Optional

# Directorios base
BASE_DIR = Path(__file__).parent.parent.parent
SRC_DIR = Path(__file__).parent.parent

# Variables de entorno críticas
TELEGRAM_BOT_TOKEN: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
FIREBASE_CREDENTIALS_PATH: Optional[str] = os.getenv("FIREBASE_CREDENTIALS_PATH")

def validate_config() -> bool:
    """Valida que la configuración mínima esté presente."""
    errors = []
    
    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN no está configurado")
    
    if not FIREBASE_CREDENTIALS_PATH:
        errors.append("FIREBASE_CREDENTIALS_PATH no está configurado")
    elif not os.path.exists(FIREBASE_CREDENTIALS_PATH):
        errors.append(f"Archivo de credenciales no encontrado: {FIREBASE_CREDENTIALS_PATH}")
    
    if errors:
        raise ValueError("\n".join(errors))
    
    return True

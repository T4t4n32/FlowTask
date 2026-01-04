import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Esto obliga a Python a leer el archivo físico .env antes que cualquier otra cosa
load_dotenv(override=True)

class Settings(BaseSettings):
    """Configuración con prioridad absoluta al archivo .env."""
    PROJECT_NAME: str = "FlowTask"
    
    TELEGRAM_BOT_TOKEN: str
    FIREBASE_PROJECT_ID: str
    FIREBASE_CREDENTIALS_PATH: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
"""Configuración central. Único lugar que lee variables de entorno."""
import os

from dotenv import load_dotenv

# Sin override: una variable real del entorno (ej. las de Railway) gana sobre el .env.
load_dotenv()


class Settings:
    # Telegram
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "").strip()
    # "1" = el proceso hace long-polling a Telegram (máquina propia, sin URL pública).
    # "0" = modo webhook (necesita URL pública; el endpoint /webhook/telegram sigue existiendo).
    TELEGRAM_POLLING: bool = os.getenv("TELEGRAM_POLLING", "0").strip() == "1"

    # IA (Google Gemini). Aliases "-latest" para no chocar con deprecaciones:
    #   gemini-flash-lite-latest = barato, suficiente para clasificar (default)
    #   gemini-flash-latest      = más potente, para tareas pesadas (ej. descomponer metas)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest").strip()

    # Base de datos. Por defecto SQLite local; en Task 3 se pasa a la URL de Supabase.
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./flowtask.db").strip()


settings = Settings()

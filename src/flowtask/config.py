"""Configuración central. Único lugar que lee variables de entorno."""
import os

from dotenv import load_dotenv

load_dotenv(override=True)


class Settings:
    # Telegram
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "").strip()

    # IA (Google Gemini)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()

    # Base de datos. Por defecto SQLite local; en Task 3 se pasa a la URL de Supabase.
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./flowtask.db").strip()


settings = Settings()

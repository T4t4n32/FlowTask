import re
from datetime import datetime
from typing import Any
import dateparser

class EventParser:
    """Clase encargada de transformar lenguaje natural en datos estructurados."""

    def parse_text(self, text: str) -> tuple[str, datetime | None]:
        """
        Analiza el texto para extraer una descripción limpia y una fecha.
        Si se menciona una hora pero no un día, asume que es hoy.
        """
        parse_settings: Any = {
            'PREFER_DATES_FROM': 'future',
            'RETURN_AS_TIMEZONE_AWARE': False,
            'LANGUAGE_DETECTION_CONFIDENCE_THRESHOLD': 0.5
        }
        
        # Intentar extraer la fecha/hora
        dt = dateparser.parse(
            text, 
            languages=['es'], 
            settings=parse_settings
        )
        
        # Lógica extra: Si hay hora pero no se especificó día, dateparser 
        # a veces necesita un empujón para no devolver None.
        clean_title = text
        
        if dt:
            # Lista de palabras clave de tiempo para limpiar el título
            time_keywords = [
                r"\bmañana\b", r"\bhoy\b", 
                r"\blunes\b", r"\bmartes\b", r"\bmiércoles\b", 
                r"\bjueves\b", r"\bviernes\b", r"\bsábado\b", r"\bdomingo\b",
                r"\ba las\s+\d{1,2}(:\d{2})?(\s*(am|pm))?",
                r"\bproximo\b", r"\bpróximo\b", r"\ben\b"
            ]
            
            for pattern in time_keywords:
                clean_title = re.sub(pattern, "", clean_title, flags=re.IGNORECASE)
        
        clean_title = " ".join(clean_title.split())
        return clean_title.strip().capitalize(), dt
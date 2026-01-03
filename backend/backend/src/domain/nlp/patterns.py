"""
Patrones para procesamiento de lenguaje natural en español.
"""
import re

DAYS_OF_WEEK = {
    "lunes": 0,
    "martes": 1,
    "miércoles": 2,
    "miercoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sábado": 5,
    "sabado": 5,
    "domingo": 6
}

PATTERNS = {
    "weekly": re.compile(r'(todos|cada|todos los)\s+los?\s+([a-záéíóú]+)s?', re.I),
    "time": re.compile(r'a las (\d{1,2})(?::(\d{2}))?\s*(am|pm)?', re.I),
    "relative_date": re.compile(r'(mañana|pasado mañana|hoy|esta tarde|esta noche)', re.I)
}

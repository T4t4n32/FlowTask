"""Extrae fecha/hora en español de un texto libre.

dateparser 1.4.x no interpreta bien "a las 9" / "9am" / "cada día a las 17:00"
(se queda con la hora actual o devuelve None). _normalize() traduce esas frases y
quita las palabras de recurrencia antes de parsear; parse_when() prefiere el
último match que no sea una duración suelta ("15 min").
ponytail: heurística de horas; en frases muy enrevesadas puede fallar. El bot
confirma la fecha interpretada para que el usuario corrija.
"""
import re
from datetime import datetime

from dateparser.search import search_dates

_SETTINGS = {
    "PREFER_DATES_FROM": "future",
    "RETURN_AS_TIMEZONE_AWARE": False,
}

_RECURRENCE = re.compile(
    r"\b(cada\s+d[ií]a|todos\s+los\s+d[ií]as|a\s+diario|diariamente|cada)\b", re.I
)
_DURATION = re.compile(r"^\d+\s*(min|minutos?|h|hs|hrs|horas?|seg|segundos?)$", re.I)


def _ampm(m: re.Match) -> str:
    h = int(m.group(1))
    ap = m.group(2).lower()
    if ap.startswith("p") and h < 12:
        h += 12
    if ap.startswith("a") and h == 12:
        h = 0
    return f"{h:02d}:00"


def _del_dia(m: re.Match) -> str:
    h = int(m.group(1))
    periodo = m.group(2).lower()
    if periodo in ("tarde", "noche") and h < 12:
        h += 12
    return f"{h:02d}:00"


def _normalize(text: str) -> str:
    t = _RECURRENCE.sub(" ", text)
    # "17hs" / "17 h" / "17hrs" -> "17:00"
    t = re.sub(
        r"\b(\d{1,2})\s*h(?:s|rs)?\b(?!\s*[:.]?\d)",
        lambda m: f"{int(m.group(1)):02d}:00",
        t,
        flags=re.I,
    )
    # "9am" / "4 p.m." -> "09:00" / "16:00"
    t = re.sub(r"\b(?:a\s+las\s+)?(\d{1,2})\s*([ap])\.?\s*m\.?\b", _ampm, t, flags=re.I)
    # "9 de la tarde/noche/mañana" -> "21:00" / "09:00"
    t = re.sub(
        r"\b(?:a\s+las\s+)?(\d{1,2})\s+de\s+la\s+(mañana|manana|tarde|noche|madrugada)\b",
        _del_dia,
        t,
        flags=re.I,
    )
    # "a las 9" a secas -> "09:00"
    t = re.sub(
        r"\ba\s+las\s+(\d{1,2})(?!\s*[:.\d])\b",
        lambda m: f"{int(m.group(1)):02d}:00",
        t,
        flags=re.I,
    )
    return t


def parse_when(text: str, now: datetime | None = None) -> datetime | None:
    """Devuelve el datetime mencionado en el texto, o None si no hay ninguno."""
    settings = dict(_SETTINGS)
    if now is not None:
        settings["RELATIVE_BASE"] = now
    try:
        found = search_dates(_normalize(text), languages=["es"], settings=settings)
    except Exception:
        return None
    if not found:
        return None
    # último match que no sea una duración suelta ("15 minutos" dentro del título)
    for matched, dt in reversed(found):
        if not _DURATION.match(matched.strip()):
            return dt
    return found[-1][1]

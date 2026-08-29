"""Códigos de vinculación de un solo uso (en memoria). El bot los emite con /vincular."""
import secrets
import time

_TTL = 600  # 10 min
_codes: dict[str, tuple[int, float]] = {}  # code -> (user_id, expira_en)


def new_code(user_id: int) -> str:
    code = secrets.token_hex(3).upper()  # 6 hex, ej. "A3F9C1"
    _codes[code] = (user_id, time.time() + _TTL)
    return code


def consume(code: str) -> int | None:
    """Devuelve el user_id y borra el código. None si no existe o caducó."""
    v = _codes.pop((code or "").strip().upper(), None)
    if v is None or v[1] < time.time():
        return None
    return v[0]

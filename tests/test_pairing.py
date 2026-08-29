"""Task 15: vinculación por código + sesión del panel web (PWA)."""
import asyncio
import time

from fastapi.testclient import TestClient

from src.flowtask import main, pairing
from src.flowtask.infrastructure.database import (
    get_or_create_user,
    new_session,
    user_from_token,
)

client = TestClient(main.app)


def test_codigo_de_un_solo_uso():
    uid = get_or_create_user("telegram", "1500")
    code = pairing.new_code(uid)
    assert pairing.consume(code) == uid
    assert pairing.consume(code) is None  # ya consumido


def test_codigo_caducado():
    uid = get_or_create_user("telegram", "1501")
    code = pairing.new_code(uid)
    pairing._codes[code] = (uid, time.time() - 1)  # forzar expiración
    assert pairing.consume(code) is None


def test_new_session_roundtrip():
    uid = get_or_create_user("telegram", "1502")
    tok = new_session(uid)
    assert user_from_token(tok) == uid
    assert user_from_token("no-existe") is None
    assert user_from_token(None) is None


def test_app_con_codigo_valido_pone_cookie_y_redirige():
    uid = get_or_create_user("telegram", "1503")
    code = pairing.new_code(uid)
    r = client.get(f"/app?code={code}", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"] == "/dashboard"
    assert "ft_token" in r.cookies


def test_app_con_codigo_malo():
    r = client.get("/app?code=ZZZZZZ", follow_redirects=False)
    assert r.status_code == 400


def test_dashboard_sin_cookie_pide_vincular():
    c = TestClient(main.app)
    r = c.get("/dashboard")
    assert r.status_code == 200 and "Vincula tu cuenta" in r.text


def test_dashboard_con_cookie_renderiza():
    uid = get_or_create_user("telegram", "1504")
    c = TestClient(main.app)
    c.cookies.set("ft_token", new_session(uid))
    r = c.get("/dashboard")
    assert r.status_code == 200 and "stats-store" in r.text


def test_api_history_sin_cookie_devuelve_vacio():
    c = TestClient(main.app)
    assert c.get("/api/history/tasks").json() == []


def test_comando_vincular_da_enlace():
    reply = asyncio.run(main.handle_incoming_message("telegram", "1505", "/vincular"))
    assert "/app?code=" in reply

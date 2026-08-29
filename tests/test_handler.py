"""Task 10: handle_incoming_message es agnóstico de plataforma."""
import asyncio

from src.flowtask import main
from src.flowtask.infrastructure.ai_engine import AIResponse


class _FakeAI:
    def __init__(self, resp: AIResponse):
        self.resp = resp

    async def classify_text(self, text: str) -> AIResponse:
        return self.resp


def _handle(text, platform="telegram", chat_id="1", name=""):
    return asyncio.run(main.handle_incoming_message(platform, chat_id, text, name))


def test_comando_equipo_no_toca_la_ia():
    r = _handle("/equipo crear MiEquipo")
    assert "MiEquipo" in r and "unir" in r


def test_list_vacio():
    assert "Todo limpio" in _handle("/list")


def test_guardar_tarea(monkeypatch):
    monkeypatch.setattr(
        main, "ai_engine",
        _FakeAI(AIResponse(intent="SAVE", category="TASK", clean_title="Comprar pan")),
    )
    r = _handle("comprar pan")
    assert "Registrado" in r and "Comprar pan" in r


def test_charla_devuelve_response_text(monkeypatch):
    monkeypatch.setattr(
        main, "ai_engine",
        _FakeAI(AIResponse(intent="CHAT", response_text="¡Hola!")),
    )
    assert _handle("hola") == "¡Hola!"


def test_habito(monkeypatch):
    monkeypatch.setattr(
        main, "ai_engine",
        _FakeAI(AIResponse(intent="SAVE", category="HABIT", clean_title="Leer", is_habit=True)),
    )
    r = _handle("leer cada dia a las 20:00")
    assert "Hábito" in r and "20:00" in r


def test_mismo_resultado_por_cualquier_plataforma(monkeypatch):
    monkeypatch.setattr(
        main, "ai_engine",
        _FakeAI(AIResponse(intent="SAVE", category="TASK", clean_title="X")),
    )
    assert _handle("x", platform="telegram", chat_id="aaa") == _handle(
        "x", platform="whatsapp", chat_id="bbb"
    )

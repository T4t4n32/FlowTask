"""Task 7: parse_when — fecha/hora en español desde texto libre."""
from datetime import datetime, timedelta

import pytest

from src.flowtask.nlp import parse_when

# Sábado 29 de agosto de 2026, 14:00
NOW = datetime(2026, 8, 29, 14, 0, 0)


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("Pagar la factura de la luz mañana a las 9am", datetime(2026, 8, 30, 9, 0)),
        ("Reunion con el jefe el viernes a las 4pm", datetime(2026, 9, 4, 16, 0)),
        ("reunion mañana a las 15:30", datetime(2026, 8, 30, 15, 30)),
        ("meditar a las 7 de la mañana", datetime(2026, 8, 30, 7, 0)),
        ("cena a las 9 de la noche", datetime(2026, 8, 29, 21, 0)),
        # hábitos: "cada día" / "15 min" no deben confundir la hora
        ("leer 15 minutos cada dia a las 17:00", datetime(2026, 8, 29, 17, 0)),
        ("ir al gym todos los dias a las 7am", datetime(2026, 8, 30, 7, 0)),
        ("Entregar informe el 5 de septiembre", datetime(2026, 9, 5, 0, 0)),
    ],
)
def test_fechas_absolutas_y_de_dia(texto, esperado):
    assert parse_when(texto, now=NOW) == esperado


def test_relativa_en_horas():
    got = parse_when("Llamar al medico en 2 horas", now=NOW)
    assert got == NOW + timedelta(hours=2)


@pytest.mark.parametrize(
    "texto",
    ["Comprar pan y huevos", "Idea para el proyecto", "Recordar la contraseña del wifi"],
)
def test_sin_fecha_devuelve_none(texto):
    assert parse_when(texto, now=NOW) is None


def test_prefiere_futuro():
    # "a las 8" ya pasó hoy (son las 14:00) -> mañana a las 8
    assert parse_when("gym a las 8", now=NOW) == datetime(2026, 8, 30, 8, 0)

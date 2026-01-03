.PHONY: help setup install dev test lint format clean run-dev check-env pre-commit

# Variables
PYTHON = python3
VENV = venv
PIP = $(VENV)/bin/pip
PYTEST = $(VENV)/bin/pytest
BLACK = $(VENV)/bin/black
FLAKE8 = $(VENV)/bin/flake8
ISORT = $(VENV)/bin/isort
PRE_COMMIT = $(VENV)/bin/pre-commit

# Comandos principales
help:
	@echo "Comandos disponibles para FlowTask:"
	@echo ""
	@echo "  make setup       - Configura el entorno de desarrollo completo"
	@echo "  make install     - Instala dependencias de producción"
	@echo "  make dev         - Instala dependencias de desarrollo"
	@echo "  make test        - Ejecuta todas las pruebas"
	@echo "  make lint        - Verifica el estilo del código"
	@echo "  make format      - Formatea el código automáticamente"
	@echo "  make clean       - Limpia archivos temporales"
	@echo "  make pre-commit  - Ejecuta pre-commit en todos los archivos"
	@echo "  make run-dev     - Inicia el servidor de desarrollo"
	@echo "  make check-env   - Verifica variables de entorno"
	@echo ""

setup: clean
	@echo "Creando entorno virtual..."
	$(PYTHON) -m venv $(VENV)
	@echo "Instalando dependencias de desarrollo..."
	$(MAKE) dev
	@echo "Instalando hooks de pre-commit..."
	$(PRE_COMMIT) install
	@echo ""
	@echo "✅ Entorno configurado correctamente."
	@echo "Activa el entorno con: source $(VENV)/bin/activate"

install:
	@echo "Instalando dependencias de producción..."
	$(PIP) install -e .

dev:
	@echo "Instalando dependencias de desarrollo..."
	$(PIP) install -e ".[dev]"

test:
	@echo "Ejecutando pruebas..."
	cd backend && $(PYTEST) tests/ -v

lint:
	@echo "Verificando estilo del código..."
	cd backend/src && $(FLAKE8) .
	cd backend/src && $(BLACK) --check .
	cd backend/src && $(ISORT) --check-only .

format:
	@echo "Formateando código..."
	cd backend/src && $(BLACK) .
	cd backend/src && $(ISORT) .

clean:
	@echo "Limpiando archivos temporales..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .eggs/

pre-commit:
	@echo "Ejecutando pre-commit en todos los archivos..."
	$(PRE_COMMIT) run --all-files

run-dev:
	@echo "🚀 Iniciando servidor de desarrollo..."
	cd backend/src && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

check-env:
	@echo "Verificando variables de entorno..."
	@if [ -z "$$TELEGRAM_BOT_TOKEN" ]; then \
		echo "❌ ERROR: TELEGRAM_BOT_TOKEN no está definido"; \
		exit 1; \
	else \
		echo "✅ TELEGRAM_BOT_TOKEN está definido"; \
	fi
	@if [ -z "$$FIREBASE_CREDENTIALS_PATH" ]; then \
		echo "❌ ERROR: FIREBASE_CREDENTIALS_PATH no está definido"; \
		exit 1; \
	else \
		echo "✅ FIREBASE_CREDENTIALS_PATH está definido"; \
	fi

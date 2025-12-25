.PHONY: help setup install dev test lint format clean docker-build docker-run init-db

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
	@echo ""

setup: clean
	@echo "Creando entorno virtual..."
	$(PYTHON) -m venv $(VENV)
	@echo "Instalando dependencias de desarrollo..."
	$(MAKE) dev
	@echo "Instalando hooks de pre-commit..."
	$(PRE_COMMIT) install
	@echo ""
	@echo "Entorno configurado correctamente."
	@echo "Activa el entorno con: source $(VENV)/bin/activate"

install:
	@echo "Instalando dependencias de producción..."
	$(PIP) install -e .

dev:
	@echo "Instalando dependencias de desarrollo..."
	$(PIP) install -e ".[dev]"

test:
	@echo "Ejecutando pruebas..."
	$(PYTEST) backend/tests/ -v --cov=backend/src --cov-report=html --cov-report=term

lint:
	@echo "Verificando estilo del código..."
	$(FLAKE8) backend/src/
	$(BLACK) --check backend/src/
	$(ISORT) --check-only backend/src/

format:
	@echo "Formateando código..."
	$(BLACK) backend/src/
	$(ISORT) backend/src/

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

# Comandos específicos del proyecto
init-db:
	@echo "Inicializando base de datos..."
	@echo "Este comando se implementará más adelante"

run-dev:
	@echo "Iniciando servidor de desarrollo..."
	@echo "Este comando se implementará más adelante"

check-env:
	@echo "Verificando variables de entorno..."
	@if [ -z "$$TELEGRAM_BOT_TOKEN" ]; then \
		echo "ERROR: TELEGRAM_BOT_TOKEN no está definido"; \
		exit 1; \
	else \
		echo "✓ TELEGRAM_BOT_TOKEN está definido"; \
	fi
	@if [ -z "$$FIREBASE_PROJECT_ID" ]; then \
		echo "ERROR: FIREBASE_PROJECT_ID no está definido"; \
		exit 1; \
	else \
		echo "✓ FIREBASE_PROJECT_ID está definido"; \
	fi

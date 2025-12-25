#!/bin/bash

echo "=== Verificación de Configuración de FlowTask ==="
echo ""

# 1. Verificar estructura de carpetas
echo "1. Estructura de carpetas:"
required_dirs=(
  ".github/workflows"
  ".github/ISSUE_TEMPLATE"
  "docs/architecture"
  "backend/src"
  "backend/tests"
  "backend/requirements"
  "scripts"
)

all_dirs_exist=true
for dir in "${required_dirs[@]}"; do
  if [ -d "$dir" ]; then
    echo "  ✓ $dir"
  else
    echo "  ✗ $dir (FALTANTE)"
    all_dirs_exist=false
  fi
done
echo ""

# 2. Verificar archivos esenciales
echo "2. Archivos esenciales:"
required_files=(
  ".gitignore"
  "LICENSE"
  "pyproject.toml"
  ".pre-commit-config.yaml"
  "Makefile"
  "README.md"
  ".github/workflows/ci.yml"
  ".github/ISSUE_TEMPLATE/bug_report.md"
  ".github/ISSUE_TEMPLATE/feature_request.md"
  ".github/PULL_REQUEST_TEMPLATE.md"
  "docs/architecture/decisions/0001-telegram-as-primary-channel.md"
)

all_files_exist=true
for file in "${required_files[@]}"; do
  if [ -f "$file" ]; then
    echo "  ✓ $file"
  else
    echo "  ✗ $file (FALTANTE)"
    all_files_exist=false
  fi
done
echo ""

# 3. Verificar entorno Python
echo "3. Entorno Python:"
if [ -d "venv" ]; then
  echo "  ✓ Entorno virtual encontrado"
  
  # Verificar Python version
  if command -v python &> /dev/null; then
    python_version=$(python --version 2>&1)
    echo "  ✓ $python_version"
  else
    echo "  ✗ Python no encontrado"
  fi
else
  echo "  ✗ Entorno virtual no encontrado (ejecuta 'make setup')"
fi
echo ""

# 4. Verificar herramientas
echo "4. Herramientas de desarrollo:"
tools=("git" "make")
for tool in "${tools[@]}"; do
  if command -v $tool &> /dev/null; then
    version=$($tool --version 2>&1 | head -n1)
    echo "  ✓ $tool: $version"
  else
    echo "  ✗ $tool no encontrado"
  fi
done
echo ""

# 5. Verificar variables de entorno
echo "5. Variables de entorno:"
env_vars=("TELEGRAM_BOT_TOKEN" "FIREBASE_CREDENTIALS_PATH")

all_env_set=true
for var in "${env_vars[@]}"; do
  if [ -n "${!var}" ]; then
    # Mostrar solo primeros y últimos caracteres por seguridad
    value="${!var}"
    if [ "$var" = "TELEGRAM_BOT_TOKEN" ]; then
      masked="${value:0:8}...${value: -4}"
    else
      masked="${value:0:20}...${value: -20}"
    fi
    echo "  ✓ $var: $masked"
  else
    echo "  ✗ $var: NO CONFIGURADA"
    all_env_set=false
  fi
done
echo ""

# Resumen
echo "=== RESUMEN ==="
if [ "$all_dirs_exist" = true ] && [ "$all_files_exist" = true ] && [ "$all_env_set" = true ]; then
  echo "✅ Configuración COMPLETA. Puedes comenzar el desarrollo."
else
  echo "⚠️  Configuración INCOMPLETA. Revisa los puntos marcados con ✗."
fi

#!/bin/bash
echo "=== VERIFICACIÓN COMPLETA DE FLOWTASK ==="
echo ""

# 1. Verificar estructura de carpetas
echo "1. Estructura de carpetas:"
check_dir() {
    if [ -d "$1" ]; then
        echo "  ✅ $1/"
        return 0
    else
        echo "  ❌ $1/ (FALTANTE)"
        return 1
    fi
}

check_dir "backend/src"
check_dir "backend/src/api"
check_dir "backend/src/core"
check_dir "backend/src/domain"
check_dir "backend/src/domain/events"
check_dir "backend/src/domain/nlp"
check_dir "backend/src/infrastructure"
check_dir "backend/tests"
check_dir "secure_credentials"

echo ""

# 2. Verificar archivos críticos
echo "2. Archivos críticos:"
check_file() {
    if [ -f "$1" ]; then
        echo "  ✅ $1"
        return 0
    else
        echo "  ❌ $1 (FALTANTE)"
        return 1
    fi
}

check_file "backend/src/main.py"
check_file "backend/src/core/config.py"
check_file "backend/src/infrastructure/firebase_client.py"
check_file "backend/src/infrastructure/telegram_client.py"
check_file "backend/src/domain/events/models.py"
check_file "backend/src/domain/nlp/parser.py"
check_file "backend/src/domain/nlp/patterns.py"
check_file "backend/tests/test_firebase.py"
check_file "backend/tests/test_telegram.py"

echo ""

# 3. Verificar __init__.py
echo "3. Archivos __init__.py:"
for dir in backend/src backend/src/api backend/src/core backend/src/domain \
           backend/src/domain/events backend/src/domain/nlp backend/src/infrastructure \
           backend/tests; do
    if [ -f "$dir/__init__.py" ]; then
        echo "  ✅ $dir/__init__.py"
    else
        echo "  ❌ $dir/__init__.py (FALTANTE)"
    fi
done

echo ""

# 4. Verificar variables de entorno
echo "4. Variables de entorno:"
if [ -n "$TELEGRAM_BOT_TOKEN" ]; then
    echo "  ✅ TELEGRAM_BOT_TOKEN configurado"
else
    echo "  ❌ TELEGRAM_BOT_TOKEN NO configurado"
fi

if [ -n "$FIREBASE_CREDENTIALS_PATH" ]; then
    echo "  ✅ FIREBASE_CREDENTIALS_PATH configurado"
    if [ -f "$FIREBASE_CREDENTIALS_PATH" ]; then
        echo "    📁 Archivo encontrado: $(basename "$FIREBASE_CREDENTIALS_PATH")"
    else
        echo "    ❌ Archivo NO encontrado en la ruta"
    fi
else
    echo "  ❌ FIREBASE_CREDENTIALS_PATH NO configurado"
fi

echo ""
echo "=== FIN DE VERIFICACIÓN ==="

#!/bin/bash
echo "=== Verificación de Estructura del Proyecto ==="
echo ""

echo "1. Estructura actual en backend/src/:"
pwd
echo ""
find . -type f -name "*.py" | sort
echo ""

echo "2. Contenido de infrastructure/:"
if [ -d "infrastructure" ]; then
    ls -la infrastructure/
    echo ""
    echo "3. Archivo __init__.py en infrastructure/:"
    if [ -f "infrastructure/__init__.py" ]; then
        echo "   ✅ Existe"
    else
        echo "   ❌ FALTA - Creando..."
        touch infrastructure/__init__.py
    fi
    echo ""
    echo "4. Archivo firebase_client.py:"
    if [ -f "infrastructure/firebase_client.py" ]; then
        echo "   ✅ Existe"
        echo "   Tamaño: $(wc -l < infrastructure/firebase_client.py) líneas"
    else
        echo "   ❌ FALTA"
    fi
else
    echo "   ❌ La carpeta infrastructure/ no existe"
    echo "   Creando estructura..."
    mkdir -p infrastructure
    touch infrastructure/__init__.py
fi

echo ""
echo "5. Path de Python:"
python -c "import sys; print('\n'.join(sys.path))"

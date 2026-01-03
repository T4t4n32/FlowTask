#!/bin/bash
echo "=== VERIFICACIÓN RÁPIDA ==="
echo "1. Python version: $(python --version)"
echo "2. Variables de entorno:"
echo "   TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN:0:10}..."
echo "   FIREBASE_CREDENTIALS_PATH: $FIREBASE_CREDENTIALS_PATH"
echo "3. Importaciones Python:"
python -c "
try:
    from backend.src.core.config import validate_config
    print('   ✅ core/config.py')
except Exception as e:
    print(f'   ❌ core/config.py: {e}')
try:
    from backend.src.domain.nlp.parser import SpanishEventParser
    print('   ✅ domain/nlp/parser.py')
except Exception as e:
    print(f'   ❌ domain/nlp/parser.py: {e}')
try:
    from backend.src.infrastructure.firebase_client import get_firestore_client
    print('   ✅ infrastructure/firebase_client.py')
except Exception as e:
    print(f'   ❌ infrastructure/firebase_client.py: {e}')
"

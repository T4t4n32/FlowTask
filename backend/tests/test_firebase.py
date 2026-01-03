"""
Pruebas simplificadas para Firebase.
"""
import os
import sys

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

def test_firebase_connection():
    """Prueba simple de conexión a Firebase."""
    try:
        from infrastructure.firebase_client import test_connection
        
        success, message = test_connection()
        if success:
            print(f"✅ {message}")
            return True
        else:
            print(f"❌ {message}")
            return False
            
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False

if __name__ == "__main__":
    test_firebase_connection()

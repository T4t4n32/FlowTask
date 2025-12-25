import os
import firebase_admin
from firebase_admin import credentials, firestore

def test_firebase_connection():
    """Prueba la conexión con Firebase usando el archivo de credenciales."""
    
    # 1. Verificar que la variable de entorno esté configurada
    creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    
    if not creds_path:
        print("✗ ERROR: FIREBASE_CREDENTIALS_PATH no está configurada")
        print("   Configúrala con: export FIREBASE_CREDENTIALS_PATH='/ruta/a/tu/archivo.json'")
        return False
    
    if not os.path.exists(creds_path):
        print(f"✗ ERROR: El archivo no existe en: {creds_path}")
        return False
    
    try:
        # 2. Inicializar Firebase con el archivo de credenciales
        print("🔧 Inicializando Firebase con archivo de credenciales...")
        cred = credentials.Certificate(creds_path)
        firebase_admin.initialize_app(cred)
        print("✓ Firebase configurado correctamente")
        
        # 3. Probar conexión a Firestore
        db = firestore.client()
        print("✓ Conexión a Firestore establecida")
        
        # 4. Crear documento de prueba
        doc_ref = db.collection("test_connection").document("flowtask_setup")
        test_data = {
            "test": True,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "project": "FlowTask MVP",
            "status": "connection_verified"
        }
        
        doc_ref.set(test_data)
        print("✓ Documento de prueba creado")
        
        # 5. Leer y verificar el documento
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            print(f"✓ Documento verificado:")
            print(f"  - ID: {doc.id}")
            print(f"  - Test: {data.get('test')}")
            print(f"  - Proyecto: {data.get('project')}")
            print(f"  - Estado: {data.get('status')}")
            if 'timestamp' in data:
                print(f"  - Timestamp: {data['timestamp']}")
            return True
        else:
            print("✗ Error: Documento no encontrado después de crearlo")
            return False
            
    except FileNotFoundError as e:
        print(f"✗ ERROR: Archivo no encontrado - {e}")
        return False
    except ValueError as e:
        print(f"✗ ERROR: Credenciales inválidas - {e}")
        print("  Verifica que el archivo JSON sea válido y no esté corrupto.")
        return False
    except Exception as e:
        print(f"✗ ERROR inesperado: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Probando conexión con Firebase...")
    print("=" * 50)
    
    # Verificar variable de entorno
    current_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "NO CONFIGURADA")
    print(f"📁 Ruta configurada: {current_path}")
    
    if test_firebase_connection():
        print("=" * 50)
        print("✅ ¡PRUEBA EXITOSA! Firebase está correctamente configurado.")
    else:
        print("=" * 50)
        print("❌ PRUEBA FALLIDA. Revisa la configuración de Firebase.")

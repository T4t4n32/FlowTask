"""
Cliente para Firebase Firestore.
"""
import os
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.firestore import Client

# Variable global para la instancia de Firestore
_firestore_client = None

def get_firestore_client() -> Client:
    """
    Obtiene o crea el cliente de Firestore.
    Usa patrón singleton para evitar múltiples inicializaciones.
    """
    global _firestore_client
    
    if _firestore_client is None:
        # Obtener ruta de credenciales
        creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        
        if not creds_path:
            raise ValueError(
                "FIREBASE_CREDENTIALS_PATH no está configurada. "
                "Configúrala con: export FIREBASE_CREDENTIALS_PATH='/ruta/a/tu/archivo.json'"
            )
        
        if not os.path.exists(creds_path):
            raise FileNotFoundError(f"Archivo de credenciales no encontrado: {creds_path}")
        
        # Inicializar Firebase (solo una vez)
        if not firebase_admin._apps:
            cred = credentials.Certificate(creds_path)
            firebase_admin.initialize_app(cred)
        
        # Crear cliente de Firestore
        _firestore_client = firestore.client()
    
    return _firestore_client

def test_connection():
    """Función de prueba para verificar la conexión."""
    try:
        client = get_firestore_client()
        # Hacer una operación simple
        doc_ref = client.collection("test_connection").document("ping")
        doc_ref.set({"ping": "pong", "timestamp": firestore.SERVER_TIMESTAMP})
        
        doc = doc_ref.get()
        if doc.exists:
            return True, "Conexión exitosa a Firestore"
        else:
            return False, "Error al verificar documento"
            
    except Exception as e:
        return False, f"Error de conexión: {str(e)}"

if __name__ == "__main__":
    # Prueba simple
    success, message = test_connection()
    print(f"{'✅' if success else '❌'} {message}")

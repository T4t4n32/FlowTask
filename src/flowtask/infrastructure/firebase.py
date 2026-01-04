import firebase_admin  # type: ignore
from firebase_admin import credentials, firestore  # type: ignore
from typing import Any
import os
from ..core.config import settings
from ..core.logger import logger

class FirebaseClient:
    """Cliente para interactuar con Google Firebase Firestore."""
    
    def __init__(self) -> None:
        if not firebase_admin._apps:
            try:
                cert_path = settings.FIREBASE_CREDENTIALS_PATH
                
                # Verificación visual en consola
                if not os.path.exists(cert_path):
                    logger.error(f"🚨 ARCHIVO NO ENCONTRADO EN: {cert_path}")
                
                cred = credentials.Certificate(cert_path)
                firebase_admin.initialize_app(cred, {
                    'projectId': settings.FIREBASE_PROJECT_ID,
                })
                logger.info(f"🔥 Firebase conectado: {settings.FIREBASE_PROJECT_ID}")
            except Exception as e:
                logger.error(f"❌ Error al conectar con Firebase: {e}")
                raise e
        
        self.db = firestore.client()

    def save_task(self, user_id: int, task_data: dict[str, Any]) -> str | None:
        """Guarda una tarea en la colección users/{id}/tasks."""
        try:
            doc_ref = (
                self.db.collection("users")
                .document(str(user_id))
                .collection("tasks")
                .document()
            )
            doc_ref.set(task_data)
            logger.info(f"💾 Tarea guardada con ID: {doc_ref.id}")
            return doc_ref.id
        except Exception as e:
            logger.error(f"❌ Error al guardar en Firestore: {e}")
            return None
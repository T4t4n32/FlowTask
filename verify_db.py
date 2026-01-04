from src.flowtask.infrastructure.database import init_db, save_to_db
from src.flowtask.infrastructure.ai_engine import AIResponse

# 1. Inicializar la base de datos (Crea el archivo .db)
print("Creando base de datos...")
init_db()

# 2. Simular un dato que viene de la IA
data_simulada = AIResponse(
    category="MANGO_REL",
    clean_title="Comprar servidores para M_A_N_G_O",
    date="2026-01-05",
    is_habit=False
)

# 3. Guardar
try:
    save_to_db(data_simulada)
    print("✅ ¡Éxito! El dato de M_A_N_G_O se guardó en SQLite.")
except Exception as e:
    print(f"❌ Error al guardar: {e}")
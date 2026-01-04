import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date

# Configuración de rutas para importar la DB
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "../"))
sys.path.append(PROJECT_ROOT)

from src.flowtask.infrastructure.database import TaskModel, DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_dashboard_status():
    db = SessionLocal()
    today = date.today()
    try:
        items = db.query(TaskModel).filter(TaskModel.created_at >= today).all()
        
        print("\n" + "═"*50)
        print(f"  FLOWTASK OS - MONITOR DE ESTADO ({today})")
        print("═"*50)
        
        if not items:
            print("\n   [ No hay registros el día de hoy ]")
        else:
            print(f"{'ID':<4} | {'CAT':<10} | {'ESTADO':<8} | {'TÍTULO'}")
            print("-" * 50)
            for item in items:
                status = "DONE ✅" if item.completed else "PEND ⏳"
                emoji = "🥭" if item.category == "MANGO_REL" else "🔄" if item.is_habit else "📌"
                print(f"{item.id:<4} | {emoji} {item.category:<7} | {status:<8} | {item.title}")
        
        print("\n" + "═"*50)
    finally:
        db.close()

def delete_all_data():
    print("\n❗ ATENCIÓN: Esta acción borrará permanentemente toda la base de datos.")
    confirm = input("Escribe 'BORRAR' para confirmar: ")
    if confirm == "BORRAR":
        db = SessionLocal()
        try:
            db.query(TaskModel).delete()
            db.commit()
            print("\n✅ Datos eliminados correctamente.")
        except Exception as e:
            print(f"\n❌ Error al borrar: {e}")
        finally:
            db.close()
    else:
        print("\n❌ Operación cancelada.")
    input("\nPresione Enter para volver...")

def main_menu():
    while True:
        clear_screen()
        show_dashboard_status()
        
        print("\n[ PANEL DE CONTROL ]")
        print("1. Refrescar Vista (Actualizar)")
        print("2. Borrar Toda la Información")
        print("3. Salir del CLI")
        
        choice = input("\nSeleccione una opción: ")
        
        if choice == "1":
            continue
        elif choice == "2":
            delete_all_data()
        elif choice == "3":
            print("Saliendo...")
            break
        else:
            print("Opción no válida.")

if __name__ == "__main__":
    main_menu()
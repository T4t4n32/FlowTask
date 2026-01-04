import os
import sys
from sqlalchemy.orm import sessionmaker

BASE_PATH = "/home/t4t4n_32/Documents/Documentos/flowtask"
sys.path.append(BASE_PATH)

from src.flowtask.infrastructure.database import TaskModel, SessionLocal

def run_cli():
    os.system('clear')
    print("══ FLOWTASK CLI ══")
    db = SessionLocal()
    try:
        items = db.query(TaskModel).order_by(TaskModel.created_at.desc()).all()
        print(f"{'ID':<3} | {'HORA':<8} | {'ESTADO':<8} | {'TITULO'}")
        print("-" * 50)
        for i in items:
            hora = i.created_at.strftime("%H:%M:%S")
            status = "✅" if i.completed else "⏳"
            print(f"{i.id:<3} | {hora:<8} | {status:<8} | {i.title}")
    finally:
        db.close()
    input("\n[Enter] Refrescar...")

if __name__ == "__main__":
    while True: run_cli()
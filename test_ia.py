import asyncio
import os
from dotenv import load_dotenv
from src.flowtask.infrastructure.ai_engine import AIEngine

load_dotenv()

async def verify_ai():
    engine = AIEngine()
    
    # Lista de pruebas para ver si clasifica bien
    test_prompts = [
        "Ir al gimnasio cada mañana",
        "Comprar el dominio para M_A_N_G_O mañana a las 10am",
        "Recordar que la IP del NAS es 192.168.1.50"
    ]
    
    print(f"--- Iniciando Verificación de FlowTask IA (Modelo: {engine.model_name}) ---")
    
    for i, prompt in enumerate(test_prompts):
        print(f"\nProbando {i+1}: '{prompt}'")
        try:
            result = await engine.classify_text(prompt)
            print(f"✅ Resultado: Categoria: {result.category} | Titulo: {result.clean_title}")
        except Exception as e:
            print(f"❌ Falló: {e}")
            
        # Un pequeño respiro para no quemar la cuota de inmediato en el test
        await asyncio.sleep(2) 

if __name__ == "__main__":
    asyncio.run(verify_ai())
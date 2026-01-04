import asyncio
import os
import time
from src.flowtask.infrastructure.ai_engine import AIEngine

async def run_test_suite():
    engine = AIEngine()
    
    # Casos de prueba diseñados para forzar diferentes categorías
    casos = [
        {"texto": "Meditar 10 minutos cada mañana", "esperado": "HABIT"},
        {"texto": "Comprar repuestos para el proyecto M_A_N_G_O", "esperado": "MANGO_REL"},
        {"texto": "Cita con el médico el viernes a las 4pm", "esperado": "TASK"},
        {"texto": "La contraseña del servidor es admin123", "esperado": "FLOW_INFO"}
    ]

    print("🚀 INICIANDO VERIFICACIÓN LOCAL DE FLOWTASK IA")
    print("-" * 50)

    for i, caso in enumerate(casos):
        start_time = time.time()
        print(f"TEST {i+1}: Analizando '{caso['texto']}'...")
        
        try:
            # Llamada al motor híbrido
            resultado = await engine.classify_text(caso['texto'])
            duration = time.time() - start_time
            
            print(f"   📊 Categoría: {resultado.category}")
            print(f"   📝 Título Limpio: {resultado.clean_title}")
            print(f"   📅 Fecha: {resultado.date}")
            print(f"   ⏱️  Tiempo de respuesta: {duration:.2f}s")
            
            # Verificación de eficiencia
            if duration < 0.1:
                print("   ⚡ [PLAN B ACTIVADO] (Respuesta local ultra rápida)")
            else:
                print("   🧠 [IA CLOUD] (Respuesta de Gemini)")

        except Exception as e:
            print(f"   ❌ ERROR CRÍTICO: {e}")
        
        print("-" * 30)

if __name__ == "__main__":
    asyncio.run(run_test_suite())
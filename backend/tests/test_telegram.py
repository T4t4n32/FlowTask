"""
Pruebas para Telegram.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

def test_telegram_bot():
    """Prueba la conexión con Telegram."""
    try:
        from infrastructure.telegram_client import TelegramClient
        
        client = TelegramClient()
        bot_info = client.get_me()
        
        if bot_info:
            print("✅ Bot configurado correctamente")
            print(f"  ID: {bot_info.get('id')}")
            print(f"  Nombre: {bot_info.get('first_name')}")
            print(f"  Username: @{bot_info.get('username')}")
            return True
        else:
            print("❌ No se pudo obtener información del bot")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_telegram_bot()

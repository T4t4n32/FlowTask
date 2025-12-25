import os
import requests

# Verificar variable de entorno
token = os.getenv("TELEGRAM_BOT_TOKEN")
if not token:
    print("ERROR: TELEGRAM_BOT_TOKEN no está definido")
    exit(1)

# Probar conexión con la API de Telegram
url = f"https://api.telegram.org/bot{token}/getMe"
try:
    response = requests.get(url, timeout=10)
    data = response.json()
    
    if data.get("ok"):
        bot_info = data["result"]
        print("✓ Bot configurado correctamente")
        print(f"  ID: {bot_info['id']}")
        print(f"  Nombre: {bot_info['first_name']}")
        print(f"  Username: @{bot_info['username']}")
        print(f"  ¿Puede unirse a grupos?: {bot_info.get('can_join_groups', 'N/A')}")
        print(f"  ¿Puede leer mensajes?: {bot_info.get('can_read_all_group_messages', 'N/A')}")
        print(f"  ¿Soporta inline?: {bot_info.get('supports_inline_queries', 'N/A')}")
    else:
        print(f"✗ Error de la API: {data.get('description')}")
        
except requests.exceptions.RequestException as e:
    print(f"✗ Error de conexión: {e}")
    exit(1)
except Exception as e:
    print(f"✗ Error inesperado: {e}")
    exit(1)

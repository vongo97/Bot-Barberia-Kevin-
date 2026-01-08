import json
import os
import sys

def verify_json():
    print("--- Verificador de JSON para Credenciales de Google ---")
    print("Este script te ayudará a verificar si el texto que estás poniendo en Render es un JSON válido.")
    print("\nInstrucciones:")
    print("1. Copia TODO el contenido de tu archivo credentials.json")
    print("2. Pégalo aquí abajo y presiona ENTER, luego Ctrl+Z (Windows) o Ctrl+D (Mac/Linux) para finalizar.")
    print("-" * 60)
    
    try:
        # Leer múltiples líneas hasta EOF
        lines = sys.stdin.readlines()
        content = "".join(lines).strip()
        
        if not content:
            print("\n❌ Error: No ingresaste nada.")
            return

        # Intentar parsear
        data = json.loads(content)
        
        print("\n✅ ¡JSON Válido!")
        print(f"Tipo detectado: {list(data.keys())}")
        
        # Verificar campos clave
        client_info = data.get('web') or data.get('installed')
        if client_info:
            print("✅ Estructura correcta (web/installed encontrada).")
            if 'client_id' in client_info:
                print(f"   - client_id: OK ({client_info['client_id'][:10]}...)")
            else:
                print("   ❌ Falta 'client_id'")
                
            if 'client_secret' in client_info:
                 print("   - client_secret: OK")
            else:
                 print("   ❌ Falta 'client_secret'")
                 
            print("\nEste texto es seguro para usar en la variable GOOGLE_CREDENTIALS_JSON.")
        else:
            print("\n⚠️ Advertencia: El JSON es válido pero no parece tener la estructura de credenciales de Google (falta clave 'web' o 'installed').")
            
    except json.JSONDecodeError as e:
        print("\n❌ Error de Sintaxis JSON:")
        print(f"{e}")
        print("\nConsejo: Asegúrate de copiar desde la primera '{' hasta la última '}'.")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")

if __name__ == "__main__":
    verify_json()

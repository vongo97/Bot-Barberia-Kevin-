import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv

# Add parent directory to path to find .env easily if needed, 
# though python-dotenv handles it if we point to it.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from the parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def test_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    
    print("--- Test de Gemini API ---")
    
    if not api_key or "TU_GEMINI_API_KEY" in api_key:
        print("❌ ERROR: No se encontró una GEMINI_API_KEY válida en el archivo .env")
        print("Por favor edita el archivo .env y agrega tu clave.")
        return

    try:
        genai.configure(api_key=api_key)
        
        # Primero, listemos los modelos disponibles para ver cuál tiene tu API Key
        print("Consultando modelos disponibles...")
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
                print(f"- {m.name}")
        
        # Intentemos usar el primero que parezca ser Gemini
        model_name = 'gemini-2.5-flash'
        
        # Si gemini-1.5-flash no está en la lista (o falló antes), intentamos buscar uno válido
        # Nota: La librería a veces espera 'models/gemini-1.5-flash' o solo 'gemini-1.5-flash'
        # Vamos a intentar hacer coincidir
        if 'models/gemini-2.5-flash' not in available_models and 'gemini-2.5-flash' not in available_models:
             print(f"⚠️ 'gemini-2.5-flash' no aparece explícitamente. Intentando buscar 'gemini-pro' o similar...")
             for m in available_models:
                 if 'gemini-2.5-flash' in m:
                     model_name = m
                     break
                 elif 'gemini-pro' in m:
                     model_name = m
        
        print(f"Probando con el modelo: {model_name}")
        model = genai.GenerativeModel(model_name)
        
        print("Enviando mensaje de prueba a Gemini...")
        response = model.generate_content("Responde solo con la palabra: FUNCIONA")
        
        print(f"Respuesta de Gemini: {response.text}")
        
        if "FUNCIONA" in response.text:
            print(f"✅ ÉXITO: La conexión con Gemini es correcta usando '{model_name}'.")
        else:
            print("⚠️ ADVERTENCIA: Gemini respondió, pero algo inesperado:", response.text)
            
    except Exception as e:
        print(f"❌ ERROR: Falló la conexión con Gemini.\nDetalle: {e}")

if __name__ == "__main__":
    test_gemini()

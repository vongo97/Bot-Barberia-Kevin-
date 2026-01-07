import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from google_services import GoogleServices

# Load env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def test_sheets():
    print("--- Test de Google Sheets ---")
    
    sheet_id = os.getenv("GOOGLE_SPREADSHEET_ID")
    creds_path = os.path.join(os.path.dirname(__file__), '..', 'credentials.json')
    
    if not os.path.exists(creds_path):
        print("❌ ERROR: No se encontró el archivo 'credentials.json'.")
        return

    if not sheet_id:
        print("❌ ERROR: GOOGLE_SPREADSHEET_ID no está definido en .env")
        return

    print(f"Probando acceso al Sheet ID: {sheet_id}")
    
    try:
        services = GoogleServices(creds_path)
        
        # Try to read metadata of the spreadsheet
        print("Leyendo información del documento...")
        sheet_metadata = services.sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        properties = sheet_metadata.get('properties')
        title = properties.get('title')
        
        print(f"✅ ÉXITO: Conexión establecida. Título del Sheet: '{title}'")
        
        # Optional: Try to verify headers in 'Hoja 1' (or whatever the first sheet is)
        sheets = sheet_metadata.get('sheets', [])
        if sheets:
            first_sheet_title = sheets[0].get('properties', {}).get('title', 'Hoja 1')
            print(f"Primera hoja encontrada: '{first_sheet_title}'")
        
    except Exception as e:
        print(f"❌ ERROR: Falló la conexión con Sheets.\nDetalle: {e}")
        print("\nPosibles causas:")
        print("1. No has compartido el Google Sheet con el email del Service Account.")
        print("2. El ID del Sheet es incorrecto.")
        print("3. La API de Sheets no está habilitada en Google Cloud.")

if __name__ == "__main__":
    test_sheets()

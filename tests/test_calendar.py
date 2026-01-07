import os
import sys
import datetime
from dotenv import load_dotenv

# Add parent directory to path to import google_services
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from google_services import GoogleServices

# Load env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def test_calendar():
    print("--- Test de Google Calendar ---")
    
    calendar_id = os.getenv("GOOGLE_CALENDAR_ID")
    creds_path = os.path.join(os.path.dirname(__file__), '..', 'credentials.json')
    
    if not os.path.exists(creds_path):
        print("❌ ERROR: No se encontró el archivo 'credentials.json' en la carpeta Python_Migration.")
        print("Descarga tus credenciales de Google Cloud Console y pon el archivo ahí.")
        return

    if not calendar_id:
        print("❌ ERROR: GOOGLE_CALENDAR_ID no está definido en .env")
        return

    print(f"Probando acceso al calendario: {calendar_id}")
    
    try:
        services = GoogleServices(creds_path)
        if not services.creds: # Check if creds loaded
             print("❌ ERROR: Falló la carga de credenciales.")
             return

        # List next 3 events to validate access
        now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
        print("Consultando próximos eventos...")
        
        events_result = services.calendar_service.events().list(
            calendarId=calendar_id, timeMin=now,
            maxResults=3, singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])

        print("✅ ÉXITO: Conexión establecida.")
        if not events:
            print("No se encontraron eventos próximos (pero la conexión funciona).")
        else:
            print(f"Se encontraron {len(events)} eventos próximos:")
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                print(f"- {event['summary']} ({start})")

    except Exception as e:
        print(f"❌ ERROR: Falló la conexión con Calendar.\nDetalle: {e}")
        print("\nPosibles causas:")
        print("1. No has compartido el calendario con el email del Service Account (mira dentro de credentials.json).")
        print("2. El ID del calendario en .env es incorrecto.")
        print("3. La API de Calendar no está habilitada en tu proyecto de Google Cloud.")

if __name__ == "__main__":
    test_calendar()

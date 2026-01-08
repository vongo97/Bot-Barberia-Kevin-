import os
import logging
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from database import Database

# Cargar variables de entorno ANTES de usarlas
load_dotenv()

logger = logging.getLogger(__name__)

# Scopes necesarios para el bot
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/spreadsheets',
    'openid', # Para identificar al usuario
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

# Configura esto en tu .env o hardcode para pruebas
# En producción debe ser tu dominio https
REDIRECT_URI = os.getenv('OAUTH_REDIRECT_URI', 'http://localhost:8000/auth/callback')
CLIENT_SECRETS_FILE = 'credentials.json'

def get_credentials_data():
    """
    Obtiene las credenciales de Google OAuth.
    Retorna el dict de credenciales o lanza una Exception con la razón del fallo.
    """
    errors = []

    # 1. Intentar variable de entorno
    env_creds = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if env_creds:
        try:
            import json
            return json.loads(env_creds)
        except json.JSONDecodeError as e:
            msg = f"Error de sintaxis en GOOGLE_CREDENTIALS_JSON: {str(e)}"
            logger.error(msg)
            errors.append(msg)
    else:
        errors.append("Variable de entorno GOOGLE_CREDENTIALS_JSON no encontrada o vacía.")

    # 2. Intentar archivo local
    if os.path.exists(CLIENT_SECRETS_FILE):
        try:
            import json
            with open(CLIENT_SECRETS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            msg = f"Error leyendo archivo {CLIENT_SECRETS_FILE}: {str(e)}"
            logger.error(msg)
            errors.append(msg)
    else:
        errors.append(f"Archivo local {CLIENT_SECRETS_FILE} no encontrado.")
    
    # Si llegamos aquí, falló todo. Lanzar excepción con detalle.
    raise Exception(" | ".join(errors))

class AuthService:
    def __init__(self):
        self.db = Database()

    def get_auth_url(self, telegram_user_id):
        """
        Genera la URL de autorización para que el usuario se loguee.
        State: Usamos el telegram_user_id como 'state' para saber quién se está logueando al volver.
        """
        creds_data = get_credentials_data()
        if not creds_data:
            logger.error(f"CRITICAL: No Google Credentials found (Env or File).")
            return None

        flow = Flow.from_client_config(
            client_config=creds_data,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
    
        # 'state' viaja a Google y vuelve intacto al callback
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=str(telegram_user_id),
            prompt='consent' # Forzar refresh_token
        )
        
        return authorization_url

    def process_callback(self, code, state_telegram_id):
        """
        Intercambia el código por tokens y los guarda en la BD vinculados al telegram_id.
        """
        try:
            # Usamos requests directamente para evitar problemas de scope mismatch
            import json
            import requests
            
            # Leer client_id y client_secret desde variable de entorno o archivo
            creds_data = get_credentials_data()
            if not creds_data:
                logger.error("No se encontraron credenciales de Google OAuth")
                return False
            
            # Puede estar bajo "web" o "installed"
            client_info = creds_data.get('web') or creds_data.get('installed')
            client_id = client_info['client_id']
            client_secret = client_info['client_secret']
            token_uri = client_info.get('token_uri', 'https://oauth2.googleapis.com/token')
            
            # Intercambiar código por token
            token_response = requests.post(token_uri, data={
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': REDIRECT_URI,
                'grant_type': 'authorization_code'
            })
            
            if token_response.status_code != 200:
                logger.error(f"Error obteniendo token: {token_response.text}")
                return False
            
            tokens = token_response.json()
            
            # Guardar en DB
            creds_to_save = {
                'token': tokens.get('access_token'),
                'refresh_token': tokens.get('refresh_token'),
                'token_uri': token_uri,
                'client_id': client_id,
                'client_secret': client_secret,
                'scopes': tokens.get('scope', '').split(' ')
            }
            
            if self.db.save_user_credentials(state_telegram_id, creds_to_save):
                logger.info(f"Credenciales guardadas para usuario Telegram: {state_telegram_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Error procesando callback OAuth: {e}")
            return False

    def get_credentials(self, telegram_user_id):
        """
        Recupera y construye el objeto Credentials listo para usar con la librería de Google.
        """
        data = self.db.get_user_credentials(telegram_user_id)
        if not data:
            return None
            
        return Credentials(
            token=data.get('token'),
            refresh_token=data.get('refresh_token'),
            token_uri=data.get('token_uri'),
            client_id=data.get('client_id'),
            client_secret=data.get('client_secret'),
            scopes=data.get('scopes')
        )

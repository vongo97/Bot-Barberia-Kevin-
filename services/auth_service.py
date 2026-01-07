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
    Obtiene las credenciales de Google OAuth desde variable de entorno o archivo.
    Prioridad: GOOGLE_CREDENTIALS_JSON (env) > credentials.json (archivo)
    """
    # Intentar desde variable de entorno primero (para Render)
    env_creds = os.getenv('GOOGLE_CREDENTIALS_JSON')
    if env_creds:
        try:
            import json
            return json.loads(env_creds)
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando GOOGLE_CREDENTIALS_JSON: {e}")
    
    # Fallback a archivo
    if os.path.exists(CLIENT_SECRETS_FILE):
        try:
            import json
            with open(CLIENT_SECRETS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error leyendo {CLIENT_SECRETS_FILE}: {e}")
    
    return None

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
            logger.error(f"No se encontró {CLIENT_SECRETS_FILE} ni GOOGLE_CREDENTIALS_JSON")
            return None

        # Crear un archivo temporal si viene de variable de entorno
        import tempfile
        temp_file = None
        try:
            if os.getenv('GOOGLE_CREDENTIALS_JSON'):
                # Crear archivo temporal para Flow.from_client_secrets_file
                import json
                temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                json.dump(creds_data, temp_file)
                temp_file.close()
                secrets_file = temp_file.name
            else:
                secrets_file = CLIENT_SECRETS_FILE

            flow = Flow.from_client_secrets_file(
                secrets_file,
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
        finally:
            # Limpiar archivo temporal si se creó
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except:
                    pass

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

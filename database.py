import sqlite3
import os
import json
import logging

# Usar ruta persistente en Render si está disponible, sino local
DB_DIR = os.getenv('DB_DIR', '.')
DB_NAME = os.path.join(DB_DIR, "ultron_memory.db")
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_name=DB_NAME):
        # Asegurar que el directorio existe
        db_dir = os.path.dirname(db_name)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Tabla para guardar credenciales de usuarios
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        telegram_id TEXT PRIMARY KEY,
                        username TEXT,
                        first_name TEXT,
                        credentials_json TEXT,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                # Tabla de configuración (clave-valor)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS config (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                ''')
                conn.commit()
        except Exception as e:
            logger.error(f"Error inicializando DB: {e}")

    # --- Config Methods ---
    def get_admin_id(self):
        """Retorna el telegram_id del admin o None si no hay."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT value FROM config WHERE key = ?', ('admin_id',))
                row = cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            logger.error(f"Error obteniendo admin_id: {e}")
            return None

    def set_admin_id(self, telegram_id, username=None, first_name=None):
        """Registra al admin. Solo funciona si no hay uno ya."""
        current_admin = self.get_admin_id()
        if current_admin:
            logger.warning("Ya existe un admin configurado.")
            return False
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO config (key, value) VALUES (?, ?)', ('admin_id', str(telegram_id)))
                # También guardamos info del usuario
                cursor.execute('''
                    INSERT OR REPLACE INTO users (telegram_id, username, first_name, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ''', (str(telegram_id), username, first_name))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error guardando admin_id: {e}")
            return False

    # --- User Credentials Methods ---
    def save_user_credentials(self, telegram_id, credentials_dict, username=None, first_name=None):
        """
        Guarda las credenciales (convertidas a dict/json) del usuario.
        """
        try:
            json_data = json.dumps(credentials_dict)
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users (telegram_id, username, first_name, credentials_json, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (str(telegram_id), username, first_name, json_data))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error guardando credenciales para {telegram_id}: {e}")
            return False

    def get_user_credentials(self, telegram_id):
        """
        Retorna el dict de credenciales o None si no existe.
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT credentials_json FROM users WHERE telegram_id = ?', (str(telegram_id),))
                row = cursor.fetchone()
                if row and row[0]:
                    return json.loads(row[0])
                return None
        except Exception as e:
            logger.error(f"Error recuperando credenciales para {telegram_id}: {e}")
            return None


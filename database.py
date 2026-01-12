import os
import sqlite3
import json
import logging
from supabase import create_client, Client

# Configuración
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        self.supabase: Client = None
        
        if self.url and self.key:
            try:
                self.supabase = create_client(self.url, self.key)
                logger.info("✅ Conexión a Supabase establecida.")
                self._check_and_migrate()
            except Exception as e:
                logger.error(f"❌ Error conectando a Supabase: {e}")
        else:
            logger.warning("⚠️ SUPABASE_URL o SUPABASE_KEY no configuradas. Usando SQLite local.")

        # Mantener referencia a SQLite para migración y backup
        self.sqlite_db = os.path.join(os.getenv('DB_DIR', '.'), "ultron_memory.db")

    def _get_sqlite_conn(self):
        return sqlite3.connect(self.sqlite_db)

    def _check_and_migrate(self):
        """Migra datos de SQLite a Supabase si es necesario."""
        if not os.path.exists(self.sqlite_db):
            return

        try:
            # Verificar si ya hay admin en Supabase
            res = self.supabase.table("config").select("value").eq("key", "admin_id").execute()
            if not res.data:
                logger.info("🚀 Iniciando migración de SQLite a Supabase...")
                with self._get_sqlite_conn() as conn:
                    cursor = conn.cursor()
                    
                    # 1. Migrar Config
                    cursor.execute("SELECT key, value FROM config")
                    configs = cursor.fetchall()
                    for k, v in configs:
                        self.supabase.table("config").upsert({"key": k, "value": v}).execute()
                    
                    # 2. Migrar Users
                    cursor.execute("SELECT telegram_id, username, first_name, credentials_json FROM users")
                    users = cursor.fetchall()
                    for tid, uname, fname, creds in users:
                        self.supabase.table("users").upsert({
                            "telegram_id": str(tid),
                            "username": uname,
                            "first_name": fname,
                            "credentials_json": creds
                        }).execute()
                    
                    # 3. Migrar Bot Info
                    cursor.execute("SELECT bot_name, owner_telegram_id, owner_name, owner_username, barberia_name, owner_phone, owner_address FROM bot_info")
                    bots = cursor.fetchall()
                    for bn, otid, on, ou, bname, oph, oad in bots:
                        self.supabase.table("bot_info").insert({
                            "bot_name": bn,
                            "owner_telegram_id": str(otid),
                            "owner_name": on,
                            "owner_username": ou,
                            "barberia_name": bname,
                            "owner_phone": oph,
                            "owner_address": oad
                        }).execute()
                
                logger.info("✅ Migración completada con éxito.")
        except Exception as e:
            logger.error(f"❌ Error durante la migración: {e}")

    # --- Config Methods ---
    def get_admin_id(self):
        if self.supabase:
            try:
                res = self.supabase.table("config").select("value").eq("key", "admin_id").execute()
                return res.data[0]['value'] if res.data else None
            except Exception as e:
                logger.error(f"Error en get_admin_id (Supabase): {e}")
        
        # Fallback a SQLite si Supabase falla o no está configurado
        try:
            with self._get_sqlite_conn() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT value FROM config WHERE key = ?', ('admin_id',))
                row = cursor.fetchone()
                return row[0] if row else None
        except: return None

    def set_admin_id(self, telegram_id, username=None, first_name=None, barberia_name=None):
        if self.get_admin_id(): return False
        
        success = False
        # Guardar en Supabase
        if self.supabase:
            try:
                self.supabase.table("config").insert({"key": "admin_id", "value": str(telegram_id)}).execute()
                self.supabase.table("users").upsert({
                    "telegram_id": str(telegram_id),
                    "username": username,
                    "first_name": first_name
                }).execute()
                self.supabase.table("bot_info").insert({
                    "bot_name": os.getenv('BOT_NAME', 'Bot Barbería'),
                    "owner_telegram_id": str(telegram_id),
                    "owner_name": first_name,
                    "owner_username": username,
                    "barberia_name": barberia_name
                }).execute()
                success = True
            except Exception as e:
                logger.error(f"Error en set_admin_id (Supabase): {e}")

        # Guardar en SQLite (Backup local)
        try:
            with self._get_sqlite_conn() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)', ('admin_id', str(telegram_id)))
                cursor.execute('INSERT OR REPLACE INTO users (telegram_id, username, first_name) VALUES (?, ?, ?)', (str(telegram_id), username, first_name))
                cursor.execute('INSERT INTO bot_info (bot_name, owner_telegram_id, owner_name, owner_username, barberia_name) VALUES (?, ?, ?, ?, ?)', 
                             (os.getenv('BOT_NAME', 'Bot Barbería'), str(telegram_id), first_name, username, barberia_name))
                conn.commit()
                success = True
        except Exception as e:
            logger.error(f"Error en set_admin_id (SQLite): {e}")
        
        return success

    def get_owner_info(self):
        if self.supabase:
            try:
                res = self.supabase.table("bot_info").select("*").order("created_at", desc=True).limit(1).execute()
                if res.data:
                    d = res.data[0]
                    return {
                        'telegram_id': d['owner_telegram_id'],
                        'name': d['owner_name'],
                        'username': d['owner_username'],
                        'barberia_name': d['barberia_name'],
                        'phone': d['owner_phone'],
                        'address': d['owner_address'],
                        'created_at': d['created_at']
                    }
            except Exception as e:
                logger.error(f"Error en get_owner_info (Supabase): {e}")

        # Fallback a SQLite
        try:
            with self._get_sqlite_conn() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT owner_telegram_id, owner_name, owner_username, barberia_name, owner_phone, owner_address, created_at FROM bot_info ORDER BY created_at DESC LIMIT 1')
                row = cursor.fetchone()
                if row:
                    return {'telegram_id': row[0], 'name': row[1], 'username': row[2], 'barberia_name': row[3], 'phone': row[4], 'address': row[5], 'created_at': row[6]}
        except: return None

    def update_owner_info(self, barberia_name=None, owner_phone=None, owner_address=None):
        admin_id = self.get_admin_id()
        if not admin_id: return False
        
        success = False
        if self.supabase:
            try:
                data = {}
                if barberia_name: data['barberia_name'] = barberia_name
                if owner_phone: data['owner_phone'] = owner_phone
                if owner_address is not None: data['owner_address'] = owner_address
                if data:
                    self.supabase.table("bot_info").update(data).eq("owner_telegram_id", str(admin_id)).execute()
                    success = True
            except Exception as e:
                logger.error(f"Error en update_owner_info (Supabase): {e}")

        # SQLite
        try:
            with self._get_sqlite_conn() as conn:
                cursor = conn.cursor()
                if barberia_name: cursor.execute('UPDATE bot_info SET barberia_name = ? WHERE owner_telegram_id = ?', (barberia_name, str(admin_id)))
                if owner_phone: cursor.execute('UPDATE bot_info SET owner_phone = ? WHERE owner_telegram_id = ?', (owner_phone, str(admin_id)))
                if owner_address is not None: cursor.execute('UPDATE bot_info SET owner_address = ? WHERE owner_telegram_id = ?', (owner_address, str(admin_id)))
                conn.commit()
                success = True
        except: pass
        
        return success

    def reset_configuration(self):
        success = False
        if self.supabase:
            try:
                self.supabase.table("config").delete().eq("key", "admin_id").execute()
                self.supabase.table("bot_info").delete().neq("id", -1).execute() # Delete all
                success = True
            except Exception as e:
                logger.error(f"Error reset (Supabase): {e}")
        
        try:
            with self._get_sqlite_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM config WHERE key = 'admin_id'")
                cursor.execute("DELETE FROM bot_info")
                conn.commit()
                success = True
        except: pass
        return success

    def save_user_credentials(self, telegram_id, credentials_dict, username=None, first_name=None):
        json_data = json.dumps(credentials_dict)
        success = False
        if self.supabase:
            try:
                self.supabase.table("users").upsert({
                    "telegram_id": str(telegram_id),
                    "username": username,
                    "first_name": first_name,
                    "credentials_json": json_data
                }).execute()
                success = True
            except Exception as e:
                logger.error(f"Error save_creds (Supabase): {e}")

        try:
            with self._get_sqlite_conn() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT OR REPLACE INTO users (telegram_id, username, first_name, credentials_json) VALUES (?, ?, ?, ?)', (str(telegram_id), username, first_name, json_data))
                conn.commit()
                success = True
        except: pass
        return success

    def get_user_credentials(self, telegram_id):
        if self.supabase:
            try:
                res = self.supabase.table("users").select("credentials_json").eq("telegram_id", str(telegram_id)).execute()
                if res.data and res.data[0]['credentials_json']:
                    return json.loads(res.data[0]['credentials_json'])
            except Exception as e:
                logger.error(f"Error get_creds (Supabase): {e}")

        try:
            with self._get_sqlite_conn() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT credentials_json FROM users WHERE telegram_id = ?', (str(telegram_id),))
                row = cursor.fetchone()
                if row and row[0]: return json.loads(row[0])
        except: pass
        return None

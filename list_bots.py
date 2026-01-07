#!/usr/bin/env python3
"""
Script de administración para listar todos los bots y sus dueños.
Útil cuando tienes múltiples bots desplegados.

Uso:
    python list_bots.py
    python list_bots.py --db ruta/a/base_de_datos.db
"""

import os
import sys
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

def list_bots(db_path=None):
    """
    Lista todos los bots y sus dueños desde la base de datos.
    """
    if db_path is None:
        # Buscar bases de datos en el directorio actual y subdirectorios
        db_files = list(Path('.').rglob('ultron_memory.db'))
        if not db_files:
            print("❌ No se encontraron bases de datos (ultron_memory.db)")
            print("   Busca en el directorio actual y subdirectorios.")
            return
        
        print(f"📊 Encontradas {len(db_files)} base(s) de datos:\n")
        
        for db_file in db_files:
            print(f"{'='*60}")
            print(f"📁 Base de datos: {db_file}")
            print(f"{'='*60}")
            try:
                conn = sqlite3.connect(str(db_file))
                cursor = conn.cursor()
                
                # Verificar si la columna owner_address existe
                cursor.execute("PRAGMA table_info(bot_info)")
                columns = [col[1] for col in cursor.fetchall()]
                has_address = 'owner_address' in columns
                
                # Construir query según las columnas disponibles
                if has_address:
                    query = '''
                        SELECT owner_telegram_id, owner_name, owner_username, 
                               barberia_name, owner_phone, owner_address, created_at, bot_name
                        FROM bot_info
                        ORDER BY created_at DESC
                        LIMIT 1
                    '''
                else:
                    query = '''
                        SELECT owner_telegram_id, owner_name, owner_username, 
                               barberia_name, owner_phone, created_at, bot_name
                        FROM bot_info
                        ORDER BY created_at DESC
                        LIMIT 1
                    '''
                
                cursor.execute(query)
                owner_row = cursor.fetchone()
                
                # Obtener admin_id de config
                cursor.execute('SELECT value FROM config WHERE key = ?', ('admin_id',))
                admin_row = cursor.fetchone()
                admin_id = admin_row[0] if admin_row else None
                
                if owner_row:
                    if has_address and len(owner_row) == 8:
                        owner_id, owner_name, owner_username, barberia_name, phone, address, created_at, bot_name = owner_row
                    elif not has_address and len(owner_row) == 7:
                        owner_id, owner_name, owner_username, barberia_name, phone, created_at, bot_name = owner_row
                        address = None
                    else:
                        # Fallback para casos edge
                        owner_id = owner_row[0] if len(owner_row) > 0 else None
                        owner_name = owner_row[1] if len(owner_row) > 1 else None
                        owner_username = owner_row[2] if len(owner_row) > 2 else None
                        barberia_name = owner_row[3] if len(owner_row) > 3 else None
                        phone = owner_row[4] if len(owner_row) > 4 else None
                        address = owner_row[5] if has_address and len(owner_row) > 5 else None
                        created_at = owner_row[6] if has_address and len(owner_row) > 6 else (owner_row[5] if len(owner_row) > 5 else None)
                        bot_name = owner_row[7] if has_address and len(owner_row) > 7 else (owner_row[6] if len(owner_row) > 6 else None)
                    
                    print(f"🤖 Bot: {bot_name or 'Bot Barbería'}")
                    print(f"👤 Dueño: {owner_name or 'N/A'}")
                    if owner_username:
                        print(f"   Usuario: @{owner_username}")
                    print(f"   ID Telegram: {owner_id}")
                    if barberia_name:
                        print(f"💈 Barbería: {barberia_name}")
                    if phone:
                        print(f"📞 Teléfono: {phone}")
                    if address:
                        print(f"📍 Dirección: {address}")
                    if created_at:
                        print(f"📅 Creado: {created_at}")
                    print(f"✅ Admin ID configurado: {admin_id == owner_id}")
                else:
                    # Si no hay info en bot_info, intentar obtener de users y config
                    if admin_id:
                        cursor.execute('''
                            SELECT telegram_id, username, first_name 
                            FROM users 
                            WHERE telegram_id = ?
                        ''', (admin_id,))
                        user_row = cursor.fetchone()
                        if user_row:
                            user_id, username, first_name = user_row
                            print(f"👤 Dueño: {first_name or 'N/A'}")
                            if username:
                                print(f"   Usuario: @{username}")
                            print(f"   ID Telegram: {user_id}")
                            print(f"⚠️  Información básica (no hay datos completos en bot_info)")
                        else:
                            print(f"⚠️  Admin ID: {admin_id} (no se encontró información del usuario)")
                    else:
                        print("❌ No hay dueño configurado")
                
                # Contar usuarios
                cursor.execute('SELECT COUNT(*) FROM users')
                user_count = cursor.fetchone()[0]
                print(f"👥 Usuarios registrados: {user_count}")
                
                conn.close()
                print()
                
            except sqlite3.Error as e:
                print(f"❌ Error leyendo {db_file}: {e}\n")
    else:
        # Leer una base de datos específica
        if not os.path.exists(db_path):
            print(f"❌ No se encontró la base de datos: {db_path}")
            return
        
        print(f"📊 Información de: {db_path}\n")
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificar si la columna owner_address existe
            cursor.execute("PRAGMA table_info(bot_info)")
            columns = [col[1] for col in cursor.fetchall()]
            has_address = 'owner_address' in columns
            
            # Construir query según las columnas disponibles
            if has_address:
                query = '''
                    SELECT owner_telegram_id, owner_name, owner_username, 
                           barberia_name, owner_phone, owner_address, created_at, bot_name
                    FROM bot_info
                    ORDER BY created_at DESC
                    LIMIT 1
                '''
            else:
                query = '''
                    SELECT owner_telegram_id, owner_name, owner_username, 
                           barberia_name, owner_phone, created_at, bot_name
                    FROM bot_info
                    ORDER BY created_at DESC
                    LIMIT 1
                '''
            
            cursor.execute(query)
            owner_row = cursor.fetchone()
            
            if owner_row:
                if has_address and len(owner_row) == 8:
                    owner_id, owner_name, owner_username, barberia_name, phone, address, created_at, bot_name = owner_row
                elif not has_address and len(owner_row) == 7:
                    owner_id, owner_name, owner_username, barberia_name, phone, created_at, bot_name = owner_row
                    address = None
                else:
                    # Fallback
                    owner_id = owner_row[0] if len(owner_row) > 0 else None
                    owner_name = owner_row[1] if len(owner_row) > 1 else None
                    owner_username = owner_row[2] if len(owner_row) > 2 else None
                    barberia_name = owner_row[3] if len(owner_row) > 3 else None
                    phone = owner_row[4] if len(owner_row) > 4 else None
                    address = owner_row[5] if has_address and len(owner_row) > 5 else None
                    created_at = owner_row[6] if has_address and len(owner_row) > 6 else (owner_row[5] if len(owner_row) > 5 else None)
                    bot_name = owner_row[7] if has_address and len(owner_row) > 7 else (owner_row[6] if len(owner_row) > 6 else None)
                
                print(f"🤖 Bot: {bot_name or 'Bot Barbería'}")
                print(f"👤 Dueño: {owner_name or 'N/A'}")
                if owner_username:
                    print(f"   Usuario: @{owner_username}")
                print(f"   ID Telegram: {owner_id}")
                if barberia_name:
                    print(f"💈 Barbería: {barberia_name}")
                if phone:
                    print(f"📞 Teléfono: {phone}")
                if address:
                    print(f"📍 Dirección: {address}")
                if created_at:
                    print(f"📅 Creado: {created_at}")
            else:
                print("❌ No se encontró información del dueño")
            
            conn.close()
        except sqlite3.Error as e:
            print(f"❌ Error: {e}")

def main():
    parser = argparse.ArgumentParser(description='Lista todos los bots y sus dueños')
    parser.add_argument('--db', type=str, help='Ruta a una base de datos específica')
    args = parser.parse_args()
    
    list_bots(args.db)

if __name__ == '__main__':
    main()

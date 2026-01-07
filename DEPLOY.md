# Despliegue en VPS - Bot Barbería

## Archivos a subir
Sube toda la carpeta `Python_Migration` a tu VPS (ej: `/opt/barber-bot`).

## Paso 1: Configurar Google Cloud
En [Google Cloud Console](https://console.cloud.google.com/) -> Credenciales:
1. Edita tu Cliente OAuth 2.0 **Web Application**.
2. Agrega esta URL en "Authorized redirect URIs":
   ```
   http://200.234.234.75:8000/auth/callback
   ```
3. Guarda cambios.

## Paso 2: En el VPS (SSH)
```bash
cd /opt/barber-bot

# Instalar dependencias
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Editar .env con tus tokens reales
nano .env  # o vim
```

## Paso 3: Iniciar servicios
### Opción A: Manual (para probar)
```bash
# Terminal 1
python auth_server.py

# Terminal 2
python bot.py
```

### Opción B: Systemd (para producción)
Crea `/etc/systemd/system/barber-bot.service`:
```ini
[Unit]
Description=Barber Bot
After=network.target

[Service]
User=root
WorkingDirectory=/opt/barber-bot
ExecStart=/opt/barber-bot/venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Crea `/etc/systemd/system/barber-auth.service`:
```ini
[Unit]
Description=Barber Auth Server
After=network.target

[Service]
User=root
WorkingDirectory=/opt/barber-bot
ExecStart=/opt/barber-bot/venv/bin/python auth_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Activa:
```bash
sudo systemctl enable barber-bot barber-auth
sudo systemctl start barber-bot barber-auth
```

## Paso 4: Probar
1. Telegram → `/start` → `/setup` → `/connect`
2. Abre el link en navegador → Loguea con Google
3. Prueba agendar una cita

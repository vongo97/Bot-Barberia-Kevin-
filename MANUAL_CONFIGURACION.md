# 📋 Manual de Configuración - Bot Barbería

## Para el Proveedor (Tú)

### Paso 1: Crear Bot en Telegram
1. Abre Telegram → Busca `@BotFather`
2. Escribe `/newbot`
3. Elige nombre (ej: "Barbería El Estilo")
4. Elige username (ej: `barberiaelestilo_bot`)
5. Guarda el **TOKEN** que te da

### Paso 2: Desplegar Instancia
```bash
# Crear carpeta para el nuevo cliente
cp -r /opt/barber-bot/Python_Migration /opt/cliente-nuevo

# Editar configuración
cd /opt/cliente-nuevo
nano .env
```

Configurar `.env`:
```ini
TELEGRAM_TOKEN=<token_del_paso_1>
GEMINI_API_KEY=<tu_api_key_gemini>
GOOGLE_CALENDAR_ID=primary
GOOGLE_SPREADSHEET_ID=<dejar_vacio_o_crear_sheet>
GENAI_MODEL=gemini-2.5-flash
OAUTH_REDIRECT_URI=http://TU_IP.nip.io:PUERTO/auth/callback
```

⚠️ **Importante**: Cada cliente debe usar un **puerto diferente** para el auth_server (8081, 8082, etc.)

### Paso 3: Crear Servicios Systemd
```bash
# Reemplaza "cliente1" con nombre único
cat > /etc/systemd/system/barber-cliente1.service << 'EOF'
[Unit]
Description=Barber Bot - Cliente1
After=network.target

[Service]
User=root
WorkingDirectory=/opt/cliente-nuevo
ExecStart=/opt/cliente-nuevo/venv/bin/python bot.py
Restart=always
[Install]
WantedBy=multi-user.target
EOF

# Similar para auth server (con puerto único)
systemctl daemon-reload
systemctl enable barber-cliente1
systemctl start barber-cliente1
```

### Paso 4: Registrar URI en Google Cloud
1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Credenciales → Tu OAuth Client
3. Agrega nueva redirect URI: `http://TU_IP.nip.io:PUERTO/auth/callback`

---

## Para el Cliente (Dueño de Barbería)

### Configuración Inicial (Solo 1 vez)
1. **Abre el bot** que te dieron en Telegram
2. Escribe `/start`
3. Escribe `/setup` → Te registra como dueño
4. Escribe `/connect` → Click en el botón → Loguea con tu Google
5. ¡Listo! Tu calendario está conectado

### Uso Diario (Admin)
- **"¿Qué tengo hoy?"** → Ver citas del día
- **"Muéstrame las citas de mañana"** → Ver agenda
- **"Cancela la cita de las 3pm"** → Cancelar cita

---

## Para Clientes Finales (Usuarios)

### Agendar Cita
1. Abre el bot en Telegram
2. Escribe: "Quiero agendar una cita"
3. El bot preguntará:
   - Nombre
   - Servicio deseado
   - Día y hora preferida
4. Recibirás confirmación

### Cancelar/Reagendar
- "Quiero cancelar mi cita"
- "Necesito cambiar mi cita para otro día"

---

## Troubleshooting

| Problema | Solución |
|----------|----------|
| Bot no responde | `systemctl restart barber-clienteX` |
| Error OAuth | Verificar redirect URI en Google Console |
| "Bot no configurado" | Cliente debe ejecutar `/setup` |
| Error de calendario | Cliente debe ejecutar `/connect` |

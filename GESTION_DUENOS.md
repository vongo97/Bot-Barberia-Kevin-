# 👥 Sistema de Gestión de Dueños de Bots

Este sistema te permite identificar y rastrear quién es el dueño de cada bot de barbería que crees.

## 🎯 Características

### Comandos Disponibles en el Bot

#### `/whoami`
Muestra quién es el dueño del bot. Cualquier usuario puede usar este comando.

**Ejemplo:**
- Si eres el dueño: "✅ Eres el dueño de este bot"
- Si no eres el dueño: "👤 Dueño del Bot: [Nombre]"

#### `/info`
Muestra información completa del dueño. **Solo el administrador puede usar este comando.**

**Muestra:**
- Nombre del dueño
- Usuario de Telegram (@username)
- ID de Telegram
- Nombre de la barbería (si está configurado)
- Teléfono (si está configurado)
- Fecha de creación

### Script de Administración

#### `list_bots.py`
Script para listar todos los bots y sus dueños desde las bases de datos.

**Uso básico:**
```bash
python list_bots.py
```

Busca automáticamente todas las bases de datos `ultron_memory.db` en el directorio actual y subdirectorios, y muestra información de cada bot.

**Uso con base de datos específica:**
```bash
python list_bots.py --db ruta/a/ultron_memory.db
```

**Ejemplo de salida:**
```
📊 Encontradas 3 base(s) de datos:

============================================================
📁 Base de datos: ./cliente1/ultron_memory.db
============================================================
🤖 Bot: Bot Barbería
👤 Dueño: Juan Pérez
   Usuario: @juanperez
   ID Telegram: 123456789
💈 Barbería: Barbería El Estilo
📅 Creado: 2026-01-07 19:00:00
✅ Admin ID configurado: True
👥 Usuarios registrados: 1

============================================================
📁 Base de datos: ./cliente2/ultron_memory.db
============================================================
...
```

## 📋 Base de Datos

El sistema guarda información en la tabla `bot_info`:

- `bot_name`: Nombre del bot
- `owner_telegram_id`: ID de Telegram del dueño
- `owner_name`: Nombre del dueño
- `owner_username`: Usuario de Telegram (@username)
- `barberia_name`: Nombre de la barbería
- `owner_phone`: Teléfono del dueño (opcional)
- `created_at`: Fecha de creación
- `updated_at`: Última actualización

## 🔧 Configuración

### Al crear un nuevo bot:

1. El dueño ejecuta `/setup` en el bot
2. El sistema guarda automáticamente:
   - ID de Telegram
   - Nombre
   - Usuario de Telegram
   - Fecha de creación

### Para agregar más información:

Puedes actualizar la información del dueño usando el método `update_owner_info()` en la base de datos, o agregar comandos adicionales al bot.

## 📁 Organización Recomendada

Para gestionar múltiples bots, organiza tus carpetas así:

```
proyecto/
├── cliente1/
│   ├── bot.py
│   ├── main.py
│   ├── ultron_memory.db
│   └── ...
├── cliente2/
│   ├── bot.py
│   ├── main.py
│   ├── ultron_memory.db
│   └── ...
└── list_bots.py  (script de administración)
```

Luego ejecuta `python list_bots.py` desde la raíz del proyecto para ver todos los bots.

## 🔍 Identificación Rápida

### Desde el Bot:
- Usa `/whoami` para ver quién es el dueño
- Usa `/info` (solo admin) para ver información completa

### Desde tu Computadora:
- Ejecuta `python list_bots.py` para ver todos los bots
- Cada base de datos muestra claramente quién es el dueño

## 💡 Tips

1. **Nombres de Barbería**: Considera agregar un comando para que el dueño configure el nombre de su barbería después del setup.

2. **Backup**: Haz backup regular de las bases de datos para no perder información de los dueños.

3. **Logging**: El sistema registra automáticamente cuando se registra un nuevo dueño en los logs.

4. **Múltiples Bots**: Si tienes muchos bots, usa el script `list_bots.py` para tener una vista general rápida.

## 🚀 Próximas Mejoras Posibles

- Comando `/setbarberia` para que el dueño configure el nombre de su barbería
- Comando `/setphone` para agregar teléfono
- Exportar lista de bots a CSV o JSON
- Dashboard web para ver todos los bots
- Notificaciones cuando se registre un nuevo dueño

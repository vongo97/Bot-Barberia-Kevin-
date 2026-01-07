# 🚀 Guía de Despliegue en Render

Esta guía te ayudará a desplegar el Bot de Barbería en Render paso a paso.

## 📋 Prerrequisitos

1. **Cuenta en Render** (gratis): [https://render.com](https://render.com)
2. **Repositorio Git** (GitHub, GitLab o Bitbucket) con el código del bot
3. **Token de Telegram Bot**: Obtener de [@BotFather](https://t.me/BotFather)
4. **API Key de Google Gemini**: Obtener de [AI Studio](https://aistudio.google.com/)
5. **Proyecto en Google Cloud** con OAuth 2.0 configurado

## 🔧 Paso 1: Configurar Google Cloud OAuth

### 1.1 Crear/Configurar OAuth 2.0 Client

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Selecciona tu proyecto (o crea uno nuevo)/
3. Ve a **APIs & Services** → **Credentials**
4. Crea o edita un **OAuth 2.0 Client ID** de tipo **Web Application**
5. En **Authorized redirect URIs**, agrega:
   ```
   https://tu-app.onrender.com/auth/callback
   ```
   ⚠️ **Nota**: Reemplaza `tu-app` con el nombre que usarás en Render. Si aún no lo sabes, puedes agregarlo después.

### 1.2 Descargar Credentials

1. Descarga el archivo JSON de credenciales OAuth 2.0
2. Renómbralo a `credentials.json`
3. **Guarda este archivo** - lo necesitarás en el siguiente paso

## 📦 Paso 2: Preparar el Repositorio

### 2.1 Subir Código a Git

Asegúrate de que tu código esté en un repositorio Git:

```bash
git add .
git commit -m "Preparar para despliegue en Render"
git push origin main
```

### 2.2 Verificar Archivos Necesarios

Asegúrate de tener estos archivos en la raíz de `Python_Migration/`:
- ✅ `render.yaml` (ya creado)
- ✅ `.renderignore` (ya creado)
- ✅ `requirements.txt`
- ✅ `main.py`
- ✅ `bot.py`
- ✅ `auth_server.py`
- ✅ Todos los demás archivos del proyecto

## 🌐 Paso 3: Desplegar en Render

### 3.1 Crear Nuevo Servicio Web

1. Inicia sesión en [Render Dashboard](https://dashboard.render.com/)
2. Click en **New +** → **Web Service**
3. Conecta tu repositorio Git (GitHub/GitLab/Bitbucket)
4. Selecciona el repositorio que contiene el bot

### 3.2 Configurar el Servicio

Render debería detectar automáticamente `render.yaml`. Si no, configura manualmente:

- **Name**: `barber-bot` (o el nombre que prefieras)
- **Region**: `Oregon` (o la más cercana a ti)
- **Branch**: `main` (o tu rama principal)
- **Root Directory**: `Python_Migration` (si el código está en esa carpeta)
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python main.py`

### 3.3 Configurar Variables de Entorno

En la sección **Environment Variables**, agrega:

#### Variables Obligatorias:

```
TELEGRAM_TOKEN=tu_token_de_telegram
GEMINI_API_KEY=tu_api_key_de_gemini
OAUTH_REDIRECT_URI=https://tu-app.onrender.com/auth/callback
```

⚠️ **Importante**: Reemplaza `tu-app` con el nombre real de tu servicio en Render.

#### Variables Opcionales:

```
GOOGLE_CALENDAR_ID=primary
GOOGLE_SPREADSHEET_ID=id_de_tu_hoja_de_calculo
GENAI_MODEL=gemini-1.5-flash
```

#### Configurar Credentials.json

Tienes **dos opciones**:

**Opción A: Variable de Entorno (Recomendado)**

1. Abre el archivo `credentials.json` que descargaste
2. Copia **todo el contenido JSON**
3. En Render, agrega la variable:
   ```
   GOOGLE_CREDENTIALS_JSON={"web":{"client_id":"...","client_secret":"..."}}
   ```
   ⚠️ **Importante**: Pega el JSON completo como una sola línea, sin saltos de línea.

**Opción B: Subir Archivo (Alternativa)**

1. En Render, ve a la sección **Environment**
2. Usa **Secrets** para subir el archivo `credentials.json`
3. O agrega el archivo directamente en el repositorio (menos seguro)

### 3.4 Configurar Disco Persistente (Opcional pero Recomendado)

Para que la base de datos SQLite persista entre reinicios:

1. En la configuración del servicio, ve a **Disk**
2. Click en **Add Disk**
3. Configura:
   - **Name**: `barber-bot-data`
   - **Mount Path**: `/opt/render/project/src/data`
   - **Size**: `1 GB` (suficiente para SQLite)

Luego, agrega la variable de entorno:
```
DB_DIR=/opt/render/project/src/data
```

### 3.5 Desplegar

1. Click en **Create Web Service**
2. Render comenzará a construir y desplegar tu aplicación
3. Espera a que el build termine (puede tomar 5-10 minutos la primera vez)

## ✅ Paso 4: Verificar el Despliegue

### 4.1 Verificar Healthcheck

1. Una vez desplegado, Render te dará una URL como: `https://tu-app.onrender.com`
2. Abre esa URL en tu navegador
3. Deberías ver: `{"status": "Auth Server Running", "service": "BarberBot Auth"}`

### 4.2 Verificar Logs

1. En el dashboard de Render, ve a **Logs**
2. Busca mensajes como:
   - `"Iniciando Bot de Telegram..."`
   - `"Bot de Telegram iniciado y escuchando (Polling)."`
   - `"Scheduler de alarmas iniciado correctamente."`

Si ves errores, revisa la sección de Troubleshooting más abajo.

### 4.3 Probar el Bot

1. Abre Telegram y busca tu bot
2. Envía `/start`
3. Si eres el dueño, envía `/setup` para configurarte como admin
4. Envía `/connect` y sigue el proceso de OAuth

## 🔄 Paso 5: Actualizar OAuth Redirect URI (Si es necesario)

Si cambiaste el nombre del servicio o la URL:

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. **APIs & Services** → **Credentials**
3. Edita tu **OAuth 2.0 Client ID**
4. Actualiza **Authorized redirect URIs** con la nueva URL:
   ```
   https://tu-nueva-url.onrender.com/auth/callback
   ```

## 🐛 Troubleshooting

### El bot no responde

- **Verifica logs**: Revisa los logs en Render para ver errores
- **Verifica TELEGRAM_TOKEN**: Asegúrate de que el token sea correcto
- **Verifica que el servicio esté "Live"**: El estado debe ser verde

### Error "No se encontró credentials.json"

- **Verifica GOOGLE_CREDENTIALS_JSON**: Asegúrate de que la variable esté configurada correctamente
- **Formato JSON**: El JSON debe estar en una sola línea, sin saltos
- **Escape de caracteres**: Si hay comillas dentro del JSON, escápalas correctamente

### Error de OAuth "redirect_uri_mismatch"

- **Verifica OAUTH_REDIRECT_URI**: Debe coincidir exactamente con la URL en Google Cloud Console
- **Verifica en Google Cloud**: La URL debe estar en "Authorized redirect URIs"
- **HTTPS**: Render siempre usa HTTPS, asegúrate de usar `https://` en la configuración

### La base de datos se reinicia

- **Configura disco persistente**: Sigue el Paso 3.4
- **Verifica DB_DIR**: Asegúrate de que la variable apunte al disco montado

### El servicio se reinicia constantemente

- **Revisa logs**: Busca errores que causen crashes
- **Verifica memoria**: El plan gratuito tiene límites de memoria
- **Verifica variables de entorno**: Todas las obligatorias deben estar configuradas

## 📊 Monitoreo

### Logs en Tiempo Real

Render proporciona logs en tiempo real. Úsalos para:
- Verificar que el bot esté funcionando
- Debuggear errores
- Monitorear actividad

### Healthcheck

El endpoint `/` actúa como healthcheck. Render lo verifica automáticamente para saber si el servicio está funcionando.

## 🔐 Seguridad

- ✅ **Nunca** subas `credentials.json` al repositorio Git
- ✅ Usa variables de entorno para todos los secretos
- ✅ El plan gratuito de Render es suficiente para empezar
- ✅ Considera actualizar a un plan de pago para producción

## 📝 Notas Importantes

1. **Plan Gratuito**: Render puede "dormir" servicios gratuitos después de 15 minutos de inactividad. El bot seguirá funcionando, pero puede tardar unos segundos en responder la primera vez.

2. **Base de Datos**: SQLite funciona bien para empezar. Para producción con múltiples clientes, considera migrar a PostgreSQL (Render lo ofrece).

3. **Actualizaciones**: Cada vez que hagas `git push`, Render desplegará automáticamente la nueva versión.

4. **Backups**: Aunque Render mantiene los datos, considera hacer backups periódicos de la base de datos SQLite.

## 🎉 ¡Listo!

Tu bot debería estar funcionando en Render. Si tienes problemas, revisa los logs y la sección de troubleshooting.

Para soporte adicional, revisa la documentación de Render: [https://render.com/docs](https://render.com/docs)

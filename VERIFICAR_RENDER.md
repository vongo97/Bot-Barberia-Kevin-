# 🔍 Verificar Configuración en Render

## Problema Actual
Render no detecta el puerto aunque el bot está funcionando. Esto sugiere que:
1. El servidor web (gunicorn) no se está iniciando
2. O Render no está usando el `render.yaml`

## ✅ Solución Aplicada

Se ha corregido `main.py` para exportar correctamente la `app` que gunicorn necesita.

## 📋 Pasos para Verificar en Render

### 1. Verificar que Render esté usando render.yaml

1. Ve al dashboard de Render
2. Selecciona tu servicio `barber-bot`
3. Ve a **Settings** → **Build & Deploy**
4. Verifica que:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120 --access-logfile - --log-level info`

### 2. Si el Start Command es diferente

Si Render tiene un comando diferente (como `python main.py`), cámbialo manualmente a:
```
gunicorn main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120 --access-logfile - --log-level info
```

### 3. Verificar Variables de Entorno

Asegúrate de que estas variables estén configuradas:
- `TELEGRAM_TOKEN`
- `GEMINI_API_KEY`
- `OAUTH_REDIRECT_URI` (debe ser `https://tu-app.onrender.com/auth/callback`)
- `GOOGLE_CREDENTIALS_JSON` (opcional, si usas variable de entorno)
- `PORT` (Render lo proporciona automáticamente, no necesitas configurarlo)

### 4. Verificar Logs

Después de hacer push de los cambios, en los logs deberías ver:

**✅ Logs Correctos:**
```
[INFO] Starting gunicorn X.X.X
[INFO] Listening at: http://0.0.0.0:XXXX
[INFO] Booting worker with pid: X
[INFO] Started server process
[INFO] Waiting for application startup.
Iniciando Bot de Telegram...
Bot de Telegram iniciado y escuchando (Polling).
[INFO] Application startup complete.
```

**❌ Si NO ves logs de gunicorn:**
- Render no está ejecutando el comando correcto
- Verifica el Start Command en Settings

### 5. Forzar Nuevo Despliegue

Si hiciste cambios:
1. Ve a **Manual Deploy** → **Deploy latest commit**
2. O haz un pequeño cambio y push:
   ```bash
   git commit --allow-empty -m "Trigger redeploy"
   git push origin main
   ```

## 🔧 Si el Problema Persiste

### Opción A: Verificar que gunicorn esté instalado

En los logs del build, busca:
```
Successfully installed gunicorn-X.X.X
```

Si no aparece, el build falló. Verifica `requirements.txt`.

### Opción B: Probar comando alternativo

Si gunicorn no funciona, prueba con uvicorn directamente (menos recomendado pero puede funcionar):

En Render Settings → Start Command:
```
uvicorn main:app --host 0.0.0.0 --port $PORT --log-level info
```

### Opción C: Verificar estructura de archivos

Asegúrate de que en Render, el directorio raíz del proyecto sea correcto. Si tu código está en `Bot barberia Kevin/`, Render necesita saberlo.

En Settings → **Root Directory**, verifica que esté configurado correctamente.

## 📝 Notas

- El bot SÍ está funcionando (se ven las peticiones getUpdates)
- El problema es solo con la detección del puerto del servidor web
- Una vez que gunicorn se inicie correctamente, Render detectará el puerto automáticamente

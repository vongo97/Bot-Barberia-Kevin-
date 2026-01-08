import os
import uvicorn
import asyncio
import logging
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from bot import create_application
from services.auth_service import AuthService

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

class DebugMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print(f"!!! DEBUG REQUEST: {request.method} {request.url} !!!")
        response = await call_next(request)
        return response

# --- FastAPI Setup ---
app = FastAPI()
app.add_middleware(DebugMiddleware)
auth_service = AuthService()

@app.get("/")
def home():
    return {"status": "BarberBot Service Running", "service": "BarberBot"}

@app.get("/auth/callback")
def auth_callback(state: str, code: str):
    """
    Callback URL que llamará Google.
    state: Trae el telegram_id del usuario que inició el proceso.
    code: El código de un solo uso para obtener el token.
    """
    logger.info(f"Recibido callback para usuario Telegram ID: {state}")
    
    success = auth_service.process_callback(code, state)
    
    if success:
        return HTMLResponse("""
        <html>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: green;">✅ ¡Conexión Exitosa!</h1>
                <p>Tu calendario de Google se ha vinculado correctamente con el Bot.</p>
                <p>Ya puedes cerrar esta ventana y volver a Telegram.</p>
            </body>
        </html>
        """)
    else:
        return HTMLResponse("""
        <html>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: red;">❌ Error al conectar</h1>
                <p>Hubo un problema guardando tus credenciales. Por favor intenta de nuevo.</p>
            </body>
        </html>
        """, status_code=500)

# --- Telegram Bot Setup ---
bot_app = create_application()

@app.on_event("startup")
async def startup_event():
    """
    Inicia el bot de Telegram cuando arranca el servidor web.
    """
    logger.info("==================================================")
    logger.info("       🚀 INICIANDO SERVIDOR MAIN.PY NUEVO 🚀      ")
    print("!!! FORCE PRINT: SERVIDOR INICIANDO - SI NO VES ESTO, NO ES EL CODIGO NUEVO !!!!")
    logger.info("==================================================")
    
    # Imprimir todas las rutas registradas para debugging
    logger.info("Rutas registradas en FastAPI:")
    for route in app.routes:
        logger.info(f" -> {route.path} [{route.name}]")
        
    if bot_app:
        logger.info("Iniciando Bot de Telegram...")
        try:
            await bot_app.initialize()
            await bot_app.start()
            # start_polling es asíncrono y no bloqueante en versions recientes de PTB si se usa así
            # Sin embargo, ptb maneja su propio loop si se usa run_polling.
            # Aquí lo integramos al loop de uvicorn/fastapi manually.
            await bot_app.updater.start_polling(drop_pending_updates=True)
            logger.info("Bot de Telegram iniciado y escuchando (Polling).")
        except Exception as e:
            logger.error(f"Error iniciando el bot: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Detiene el bot correctamente al apagar el servidor.
    """
    if bot_app:
        logger.info("Deteniendo Bot de Telegram...")
        try:
            await bot_app.updater.stop()
            await bot_app.stop()
            await bot_app.shutdown()
            logger.info("Bot detenido.")
        except Exception as e:
            logger.error(f"Error deteniendo el bot: {e}")

@app.get("/debug-routes")
def debug_routes():
    """Lista todas las rutas registradas para debugging."""
    routes = []
    for route in app.routes:
        routes.append(str(route.path))
    return {"registered_routes": routes}

if __name__ == "__main__":
    # Desarrollo local: usar uvicorn directamente
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Iniciando servidor web en puerto {port} (modo desarrollo)...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True,
        loop="asyncio"
    )

import os
import uvicorn
import asyncio
import logging
from auth_server import app as fastapi_app
from bot import create_application

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Exportar app para gunicorn (necesario para: gunicorn main:app)
app = fastapi_app

# Crear la aplicación del bot
bot_app = create_application()

@fastapi_app.on_event("startup")
async def startup_event():
    """
    Inicia el bot de Telegram cuando arranca el servidor web.
    """
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

@fastapi_app.on_event("shutdown")
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

# Nota: En producción (Render), gunicorn importa este módulo directamente
# y ejecuta la app. Los eventos @app.on_event("startup") se ejecutan automáticamente.
# Este bloque solo se usa para desarrollo local.
if __name__ == "__main__":
    # Desarrollo local: usar uvicorn directamente
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Iniciando servidor web en puerto {port} (modo desarrollo)...")
    uvicorn.run(
        fastapi_app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True,
        loop="asyncio"
    )

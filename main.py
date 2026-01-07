import os
import uvicorn
import asyncio
import logging
from auth_server import app
from bot import create_application

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear la aplicación del bot
bot_app = create_application()

@app.on_event("startup")
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

if __name__ == "__main__":
    # Inicia el servidor web (Auth + Healthchecks)
    # El bot se inicia en el evento 'startup'
    # Render proporciona PORT como variable de entorno
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

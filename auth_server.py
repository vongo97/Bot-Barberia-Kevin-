from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import uvicorn
import logging
from services.auth_service import AuthService

# Configuración de logs para ver lo que pasa
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
auth_service = AuthService()

@app.get("/")
def home():
    return {"status": "Auth Server Running", "service": "BarberBot Auth"}

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

if __name__ == "__main__":
    # Correr en puerto 8000
    print("Iniciando Auth Server en puerto 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

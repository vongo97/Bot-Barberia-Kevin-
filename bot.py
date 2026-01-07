import os
import logging
import asyncio
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import google.generativeai as genai

from google_services import GoogleServices
from agent import BarberAgent
from services.auth_service import AuthService
from database import Database
from services.scheduler_service import SchedulerService

# Load environment variables
load_dotenv()

# Configure Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global DB instance
db = Database()

# Helper to download Telegram files
async def download_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_file = await update.message.effective_attachment.get_file()
    
    ext = ""
    if update.message.voice: ext = ".ogg"
    elif update.message.audio: ext = ".mp3"
    elif update.message.photo: ext = ".jpg"
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as f:
        file_path = f.name
        
    await new_file.download_to_drive(file_path)
    return file_path

# Helper for Gemini Transcription/Analysis (multimodal)
async def analyze_media(file_path: str, prompt: str, api_key: str):
    genai.configure(api_key=api_key)
    uploaded_file = genai.upload_file(path=file_path)
    
    while uploaded_file.state.name == "PROCESSING":
        await asyncio.sleep(1)
        uploaded_file = genai.get_file(uploaded_file.name)
        
    model = genai.GenerativeModel(model_name=os.getenv('GENAI_MODEL', 'gemini-1.5-flash'))
    response = model.generate_content([prompt, uploaded_file])
    return response.text

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = db.get_admin_id()
    if not admin_id:
        await update.message.reply_text(
            "👋 ¡Bienvenido!\n\n"
            "Este bot necesita ser configurado por primera vez.\n"
            "Si eres el dueño de esta barbería, escribe /setup para comenzar."
        )
    else:
        await update.message.reply_text("¡Hola! Soy el asistente virtual de la barbería. ¿En qué puedo ayudarte hoy?")

async def setup_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando para que el PRIMER usuario se registre como ADMIN (dueño del bot).
    Solo funciona una vez. Después de eso, queda bloqueado.
    """
    user = update.effective_user
    user_id = str(user.id)
    username = user.username or ""
    first_name = user.first_name or ""

    # Verificar si ya hay un admin
    current_admin = db.get_admin_id()
    if current_admin:
        await update.message.reply_text("⛔ Este bot ya tiene un dueño configurado.")
        return

    # Registrar como admin
    success = db.set_admin_id(user_id, username, first_name)
    if success:
        logger.info(f"Nuevo admin registrado: {user_id} ({first_name} @{username})")
        await update.message.reply_text(
            f"✅ ¡Perfecto, {first_name}! Ahora eres el administrador de este bot.\n\n"
            "El siguiente paso es conectar tu Google Calendar.\n"
            "Escribe /connect para hacerlo."
        )
    else:
        await update.message.reply_text("❌ Error al registrarte como admin. Intenta de nuevo.")

async def connect_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando SOLO para el ADMIN (Barbero). Genera el link para conectar su Google Calendar.
    """
    user_id = str(update.effective_user.id)
    admin_id = db.get_admin_id()
    
    if not admin_id:
        await update.message.reply_text("⚠️ Primero debes configurar el bot con /setup.")
        return
        
    if user_id != admin_id:
        await update.message.reply_text("⛔ Este comando es solo para el administrador del bot.")
        return

    auth_service = AuthService()
    auth_url = auth_service.get_auth_url(user_id)
    
    if auth_url:
        keyboard = [
            [InlineKeyboardButton("🔗 Conectar Google Calendar", url=auth_url)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Para que el bot pueda agendar citas, necesitamos permiso para acceder a tu Google Calendar.\n\nHaz clic en el botón de abajo para autorizar:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "❌ Error: No se encontraron las credenciales de Google OAuth.\n"
            "Por favor, verifica que GOOGLE_CREDENTIALS_JSON esté configurado o que el archivo credentials.json exista."
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text_input = ""

    # --- 1. Verificar si hay un ADMIN configurado en la DB ---
    admin_id = db.get_admin_id()
    if not admin_id:
        await update.message.reply_text("⚠️ Este bot no está configurado. Pídele al dueño que ejecute /setup.")
        return

    # --- 2. Verificar si el ADMIN ya conectó su calendario ---
    auth_service = AuthService()
    admin_creds = auth_service.get_credentials(admin_id)
    
    if not admin_creds:
        if user_id == admin_id:
             await update.message.reply_text("⚠️ Aún no has conectado tu calendario. Usa /connect para configurarlo.")
        else:
             await update.message.reply_text("🚧 La barbería está en mantenimiento (calendario no conectado). Intenta más tarde.")
        return

    # --- 3. Instanciar servicios con las credenciales DEL ADMIN ---
    services = GoogleServices(credentials_object=admin_creds)
    
    # Determinar si es admin o cliente
    is_admin_user = (user_id == admin_id)
    
    # Callback para avisar al barbero cuando alguien agende
    def notify_admin(summary, start_time):
        msg = f"🆕 *Nueva Cita Agendada:*\n{summary}\n📅 Fecha: {start_time}"
        # Usamos context.application para enviar el mensaje de forma asíncrona
        context.application.create_task(
            context.bot.send_message(chat_id=admin_id, text=msg, parse_mode='Markdown')
        )

    agent_controller = BarberAgent(
        api_key=os.getenv("GEMINI_API_KEY"),
        google_services=services,
        is_admin=is_admin_user,
        notify_admin_callback=notify_admin
    )
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        if update.message.voice or update.message.audio:
            file_path = await download_file(update, context)
            logger.info(f"Audio downloaded: {file_path}")
            text_input = await analyze_media(
                file_path, 
                "Transcribe el siguiente audio exactamente.", 
                os.getenv("GEMINI_API_KEY")
            )
            os.remove(file_path)
            logger.info(f"Audio transcription: {text_input}")
            
        elif update.message.photo:
            update.message.effective_attachment = update.message.photo[-1] 
            file_path = await download_file(update, context)
            logger.info(f"Image downloaded: {file_path}")
            text_input = await analyze_media(
                file_path,
                "Describe esta imagen en el contexto de una barbería (ej: corte de pelo deseado)",
                os.getenv("GEMINI_API_KEY")
            )
            os.remove(file_path)
            logger.info(f"Image analysis: {text_input}")
            text_input = f"<imagen>\n{text_input}\n</imagen>"
            
        elif update.message.text:
            text_input = update.message.text
            
        else:
            await update.message.reply_text("Lo siento, no puedo procesar este tipo de mensaje.")
            return

        response_text = agent_controller.process_message(user_id, text_input)
        await update.message.reply_text(response_text)

    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text("Ocurrió un error procesando tu solicitud.")

async def post_init(application):
    """
    Se ejecuta después de que el bot inicia.
    Ideal para arrancar el scheduler dentro del event loop.
    """
    from services.auth_service import AuthService
    auth_service = AuthService()
    scheduler = SchedulerService(application, db, auth_service)
    scheduler.start()
    logger.info("Scheduler de alarmas iniciado correctamente.")

def create_application():
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN not found in .env")
        return None

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(post_init).build()
    
    start_handler = CommandHandler('start', start)
    setup_handler = CommandHandler('setup', setup_bot)
    connect_handler = CommandHandler('connect', connect_calendar)
    message_handler = MessageHandler(filters.TEXT | filters.VOICE | filters.PHOTO | filters.AUDIO, handle_message)
    
    application.add_handler(start_handler)
    application.add_handler(setup_handler)
    application.add_handler(connect_handler)
    application.add_handler(message_handler)

    return application

if __name__ == '__main__':
    application = create_application()
    if application:
        print("Bot is running...")
        try:
            application.run_polling(drop_pending_updates=True) 
        except Exception as e:
            logger.error(f"Critical Error in polling: {e}")


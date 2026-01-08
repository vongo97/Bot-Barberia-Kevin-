import os
import logging
import asyncio
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler
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

# Estados para el formulario de setup
WAITING_BARBERIA, WAITING_PHONE, WAITING_ADDRESS = range(3)

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
    Inicia el proceso de registro del dueño del bot.
    Verifica si ya hay un admin y si no, inicia el formulario interactivo.
    """
    user = update.effective_user
    user_id = str(user.id)
    username = user.username or ""
    first_name = user.first_name or ""

    # Verificar si ya hay un admin
    current_admin = db.get_admin_id()
    if current_admin:
        await update.message.reply_text("⛔ Este bot ya tiene un dueño configurado.")
        return ConversationHandler.END

    # Limpiar datos previos para evitar errores de autocompletado de intentos fallidos
    context.user_data.clear()
    
    # Guardar información del usuario en el contexto para usarla después
    context.user_data['setup_user_id'] = user_id
    context.user_data['setup_username'] = username
    context.user_data['setup_first_name'] = first_name

    # Iniciar formulario
    await update.message.reply_text(
        f"👋 ¡Hola, {first_name}!\n\n"
        "Vamos a configurar tu bot de barbería paso a paso.\n\n"
        "📝 *Paso 1 de 3*\n"
        "¿Cuál es el nombre de tu barbería?\n\n"
        "💡 Escribe el nombre completo de tu negocio.\n"
        "Ejemplo: 'Barbería El Estilo' o 'Cortes y Estilos'",
        parse_mode='Markdown'
    )
    
    return WAITING_BARBERIA

async def receive_barberia_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe y valida el nombre de la barbería."""
    barberia_name = update.message.text.strip()
    
    # Validación básica
    if not barberia_name or len(barberia_name) < 2:
        await update.message.reply_text(
            "❌ El nombre de la barbería debe tener al menos 2 caracteres.\n"
            "Por favor, escribe el nombre de tu barbería:"
        )
        return WAITING_BARBERIA
    
    if len(barberia_name) > 100:
        await update.message.reply_text(
            "❌ El nombre es demasiado largo (máximo 100 caracteres).\n"
            "Por favor, escribe un nombre más corto:"
        )
        return WAITING_BARBERIA
    
    # Guardar en contexto temporal
    context.user_data['setup_barberia_name'] = barberia_name
    
    await update.message.reply_text(
        f"✅ *Nombre guardado:* {barberia_name}\n\n"
        "📝 *Paso 2 de 3*\n"
        "¿Cuál es tu número de teléfono de contacto?\n\n"
        "💡 Puedes escribir tu teléfono (ej: +57 300 123 4567)\n"
        "o escribir *'omitir'* si no quieres registrar uno.",
        parse_mode='Markdown'
    )
    return WAITING_PHONE

async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe y valida el teléfono (opcional)."""
    phone = update.message.text.strip()
    
    # Permitir omitir
    if phone.lower() in ['omitir', 'skip', 'no', 'n', '']:
        context.user_data['setup_phone'] = None
    else:
        # Validación básica de teléfono (solo verificar que tenga números)
        phone_clean = ''.join(filter(str.isdigit, phone))
        if len(phone_clean) < 7:
            await update.message.reply_text(
                "❌ El número de teléfono parece inválido.\n"
                "Por favor, escribe un número válido o 'omitir' para saltar:"
            )
            return WAITING_PHONE
        context.user_data['setup_phone'] = phone
    
    # Preguntar por dirección (opcional)
    await update.message.reply_text(
        "✅ *Teléfono registrado!*\n\n" if context.user_data.get('setup_phone') else "✅ *Paso omitido.*\n\n"
        "📝 *Paso 3 de 3*\n"
        "¿Cuál es la dirección física de tu barbería?\n\n"
        "💡 Escribe la dirección exacta (ej: 'Calle 10 #20-30, Ciudad')\n"
        "o escribe *'omitir'* para finalizar sin dirección.",
        parse_mode='Markdown'
    )
    
    return WAITING_ADDRESS

async def receive_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe la dirección (opcional) y finaliza el registro."""
    address = update.message.text.strip()
    
    # Permitir omitir
    if address.lower() in ['omitir', 'skip', 'no', 'n', '']:
        context.user_data['setup_address'] = None
    else:
        context.user_data['setup_address'] = address
    
    # Obtener datos del contexto
    user_id = context.user_data.get('setup_user_id')
    username = context.user_data.get('setup_username', '')
    first_name = context.user_data.get('setup_first_name', '')
    barberia_name = context.user_data.get('setup_barberia_name')
    phone = context.user_data.get('setup_phone')
    
    # Registrar como admin con toda la información
    success = db.set_admin_id(user_id, username, first_name, barberia_name=barberia_name)
    
    if success:
        # Actualizar teléfono y dirección si se proporcionaron
        if phone or context.user_data.get('setup_address') is not None:
            db.update_owner_info(
                owner_phone=phone,
                owner_address=context.user_data.get('setup_address')
            )
        
        logger.info(f"Nuevo admin registrado: {user_id} ({first_name} @{username}) - Barbería: {barberia_name}")
        
        # Mensaje de confirmación
        confirm_text = (
            f"🎉 ¡Felicidades, {first_name}! Ya eres el Administrador.\n\n"
            f"He guardado la información de tu negocio:\n"
            f"💈 *{barberia_name}*\n"
        )
        
        if phone:
            confirm_text += f"📞 Teléfono: {phone}\n"
        if context.user_data.get('setup_address'):
            confirm_text += f"📍 Dirección: {context.user_data['setup_address']}\n"
        
        confirm_text += (
            "\n🚀 *¡Tu bot está casi listo!*\n\n"
            "Solo falta un último detalle: conectarlo con tu cuenta de Google.\n"
            "Esto permitirá que el bot agiende citas automáticamente en tu calendario.\n\n"
            "👉 Escribe /connect para vincular tu cuenta ahora."
        )
        
        await update.message.reply_text(confirm_text, parse_mode='Markdown')
        
        # Limpiar datos temporales
        context.user_data.clear()
        
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            "❌ Error al guardar tu información. Por favor, intenta de nuevo con /setup."
        )
        context.user_data.clear()
        return ConversationHandler.END

async def cancel_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela el proceso de setup."""
    # Verificar si hay una conversación activa
    if context.user_data.get('setup_user_id'):
        context.user_data.clear()
        await update.message.reply_text(
            "❌ Proceso de configuración cancelado.\n"
            "Puedes volver a iniciarlo cuando quieras con /setup."
        )
        return ConversationHandler.END
    else:
        # Si no hay conversación activa, solo informar
        await update.message.reply_text(
            "ℹ️ No hay ningún proceso de configuración en curso.\n"
            "Usa /setup para comenzar a configurar el bot."
        )
        return ConversationHandler.END

async def show_owner_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando para mostrar información del dueño del bot.
    Solo el admin puede ver esta información.
    """
    user_id = str(update.effective_user.id)
    admin_id = db.get_admin_id()
    
    if not admin_id:
        await update.message.reply_text("⚠️ Este bot no está configurado. Usa /setup para configurarlo.")
        return
    
    if user_id != admin_id:
        await update.message.reply_text("⛔ Este comando es solo para el administrador del bot.")
        return
    
    owner_info = db.get_owner_info()
    if owner_info:
        info_text = "📋 *Información del Bot*\n\n"
        info_text += f"👤 *Dueño:* {owner_info.get('name', 'N/A')}\n"
        if owner_info.get('username'):
            info_text += f"📱 *Usuario:* @{owner_info['username']}\n"
        info_text += f"🆔 *ID Telegram:* `{owner_info.get('telegram_id', 'N/A')}`\n"
        if owner_info.get('barberia_name'):
            info_text += f"💈 *Barbería:* {owner_info['barberia_name']}\n"
        if owner_info.get('phone'):
            info_text += f"📞 *Teléfono:* {owner_info['phone']}\n"
        if owner_info.get('address'):
            info_text += f"📍 *Dirección:* {owner_info['address']}\n"
        if owner_info.get('created_at'):
            info_text += f"📅 *Creado:* {owner_info['created_at']}\n"
        
        await update.message.reply_text(info_text, parse_mode='Markdown')
    else:
        await update.message.reply_text("⚠️ No se encontró información del dueño en la base de datos.")

async def show_whoami(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando para que cualquier usuario vea quién es el dueño del bot.
    """
    admin_id = db.get_admin_id()
    
    if not admin_id:
        await update.message.reply_text("⚠️ Este bot no está configurado aún.")
        return
    
    user_id = str(update.effective_user.id)
    is_admin = (user_id == admin_id)
    
    if is_admin:
        owner_info = db.get_owner_info()
        if owner_info:
            text = "✅ *Eres el dueño de este bot*\n\n"
            text += f"👤 Nombre: {owner_info.get('name', 'N/A')}\n"
            if owner_info.get('barberia_name'):
                text += f"💈 Barbería: {owner_info['barberia_name']}\n"
            text += f"\nUsa /info para ver información completa."
            await update.message.reply_text(text, parse_mode='Markdown')
        else:
            await update.message.reply_text("✅ Eres el administrador de este bot.")
    else:
        owner_info = db.get_owner_info()
        if owner_info:
            text = f"👤 *Dueño del Bot:* {owner_info.get('name', 'N/A')}\n"
            if owner_info.get('barberia_name'):
                text += f"💈 *Barbería:* {owner_info['barberia_name']}\n"
            await update.message.reply_text(text, parse_mode='Markdown')
        else:
            await update.message.reply_text("Este bot pertenece a otro usuario.")

async def reset_bot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando para resetear el bot (Borrar dueño).
    """
    user_id = str(update.effective_user.id)
    admin_id = db.get_admin_id()
    
    # Solo el admin actual puede borrarlo (o si nadie es admin, pero eso es redundante)
    if admin_id and user_id != admin_id:
        await update.message.reply_text("⛔ Solo el dueño actual puede resetear el bot.")
        return

    success = db.reset_configuration()
    if success:
        await update.message.reply_text(
            "🗑️ *Bot receteado correctamente.*\n\n"
            "La configuración del dueño ha sido borrada.\n"
            "Ahora puedes usar /setup para registrar un nuevo dueño.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Error al intentar resetear el bot.")

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
    try:
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
    except Exception as e:
        # Aquí capturamos el error detallado de get_credentials_data
        error_msg = str(e)
        max_len = 3000 # Evitar mensajes muy largos
        if len(error_msg) > max_len: error_msg = error_msg[:max_len] + "..."
        
        await update.message.reply_text(
            f"❌ *Error de Autenticación Detallado:*\n\n"
            f"`{error_msg}`\n\n"
            "Por favor, revisa tus variables de entorno en Render.",
            parse_mode='Markdown'
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
    
    # ConversationHandler para el formulario de setup
    setup_conversation = ConversationHandler(
        entry_points=[CommandHandler('setup', setup_bot)],
        states={
            WAITING_BARBERIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_barberia_name)],
            WAITING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone)],
            WAITING_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_address)],
        },
        fallbacks=[CommandHandler('cancel', cancel_setup)],
        name="setup_conversation",
        persistent=False
    )
    
    start_handler = CommandHandler('start', start)
    connect_handler = CommandHandler('connect', connect_calendar)
    info_handler = CommandHandler('info', show_owner_info)
    whoami_handler = CommandHandler('whoami', show_whoami)
    reset_handler = CommandHandler('reset', reset_bot_command)
    cancel_handler = CommandHandler('cancel', cancel_setup)
    message_handler = MessageHandler(filters.TEXT | filters.VOICE | filters.PHOTO | filters.AUDIO, handle_message)
    
    # Agregar handlers (el ConversationHandler debe ir antes del message_handler)
    application.add_handler(start_handler)
    application.add_handler(setup_conversation)
    application.add_handler(connect_handler)
    application.add_handler(info_handler)
    application.add_handler(whoami_handler)
    application.add_handler(reset_handler)
    application.add_handler(cancel_handler)
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


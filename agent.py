import os
import google.generativeai as genai
import datetime
import logging
from prompts import SYSTEM_PROMPT, ADMIN_PROMPT, CUSTOMER_PROMPT
from google_services import GoogleServices

# Load logger
logger = logging.getLogger(__name__)

class BarberAgent:
    def __init__(self, api_key: str, google_services: GoogleServices, is_admin: bool = False, notify_admin_callback=None):
        genai.configure(api_key=api_key)
        self.services = google_services
        self.sessions = {} # user_id -> chat_session
        self.is_admin = is_admin
        self.notify_admin_callback = notify_admin_callback

        # Environment variables for IDs
        self.CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
        self.SPREADSHEET_ID = os.getenv('GOOGLE_SPREADSHEET_ID')

        # Define tools list for Gemini
        self.tools = [
            self.create_event,
            self.delete_event,
            self.check_availability,
            self.log_to_sheet
        ]
        
        # Select prompt based on role
        if is_admin:
            prompt_template = ADMIN_PROMPT
            logger.info("Agent initialized in ADMIN mode")
        else:
            prompt_template = CUSTOMER_PROMPT
            logger.info("Agent initialized in CUSTOMER mode")
        
        formatted_prompt = prompt_template.format(current_time=datetime.datetime.now())
        
        self.model = genai.GenerativeModel(
            model_name=os.getenv('GENAI_MODEL', 'gemini-1.5-flash'),
            tools=self.tools,
            system_instruction=formatted_prompt
        )

    def get_session(self, user_id):
        # Prefix with role to separate admin/customer conversations
        session_key = f"{'admin' if self.is_admin else 'customer'}_{user_id}"
        if session_key not in self.sessions:
            self.sessions[session_key] = self.model.start_chat(enable_automatic_function_calling=True)
        return self.sessions[session_key]

    # --- Tool Wrappers ---

    def create_event(self, summary: str, description: str, start_time: str, end_time: str):
        """
        Creates a new calendar event.
        Args:
            summary: Title of the event (e.g., "Corte de pelo - Juan").
            description: Details about the appointment.
            start_time: Start time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS).
            end_time: End time in ISO 8601 format.
        """
        # Append Telegram ID reference to description for the scheduler
        if hasattr(self, 'current_user_id') and self.current_user_id:
            description = f"{description}\n\nRef: {self.current_user_id}"
            
        result = self.services.create_event(self.CALENDAR_ID, summary, description, start_time, end_time)
        
        # Immediate notification for the barber
        if self.notify_admin_callback and not self.is_admin:
            try:
                # We can't await inside the tool if it's called synchronously by Gemini in a loop,
                # but process_message is where it's called. Wait, send_message is synchronous in the current setup.
                # Actually, our notify_admin_callback will be a regular function that eventually uses asyncio.create_task or equivalent.
                self.notify_admin_callback(summary, start_time)
            except Exception as e:
                logger.error(f"Error in notify_admin_callback: {e}")
                
        return result

    def delete_event(self, event_id: str):
        """
        Deletes a calendar event by its ID.
        Args:
            event_id: The unique identifier of the event to delete.
        """
        logger.info(f"Tool Call: delete_event {event_id}")
        return self.services.delete_event(self.CALENDAR_ID, event_id)

    def check_availability(self, time_min: str, time_max: str):
        """
        Checks calendar availability between two times.
        Args:
            time_min: Start of the range to check (ISO 8601).
            time_max: End of the range to check (ISO 8601).
        Returns:
            List of events found in that range.
        """
        logger.info(f"Tool Call: check_availability {time_min} to {time_max}")
        return self.services.check_availability(self.CALENDAR_ID, time_min, time_max)

    def log_to_sheet(self, nombre: str, servicio: str, precio: str, hora: str, estatus: str, dia: str, celular: str, event_id: str):
        """
        Logs an action (appointment, cancellation, etc.) to Google Sheets.
        Args:
            nombre: Customer name.
            servicio: Service name.
            precio: Price of the service.
            hora: Time of service (HH:mm:ss).
            estatus: Status ('agendado', 'eliminado', 'actualizado').
            dia: Date of service (YYYY-MM-DD).
            celular: Customer phone number (Telegram ID).
            event_id: Google Calendar Event ID.
        """
        logger.info(f"Tool Call: log_to_sheet {nombre} - {estatus}")
        if not self.SPREADSHEET_ID:
            return "Error: SPREADSHEET_ID not configured."
            
        RANGE = "Hoja 1!A:I" # Adjust if your sheet name is different
        values = [nombre, servicio, precio, hora, estatus, dia, celular, event_id, "Python-Bot"]
        return self.services.log_to_sheet(self.SPREADSHEET_ID, RANGE, values)

    def process_message(self, user_id: str, text: str):
        """
        Process a user message and return the agent's response.
        """
        self.current_user_id = user_id
        session = self.get_session(user_id)
        
        # Inject current time and User ID context
        current_context = f"[System: Current Time: {datetime.datetime.now()}, User_ID: {user_id}]\nUser: {text}"
        
        try:
            response = session.send_message(current_context)
            return response.text
        except Exception as e:
            logger.error(f"Error in chat session: {e}")
            return "Lo siento, tuve un problema procesando tu mensaje. Intenta de nuevo."

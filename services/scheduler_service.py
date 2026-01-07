import logging
import datetime
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from database import Database
from google_services import GoogleServices
from services.auth_service import AuthService

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self, bot_app, db: Database, auth_service: AuthService):
        self.bot_app = bot_app
        self.db = db
        self.auth_service = auth_service
        self.scheduler = AsyncIOScheduler()
        self.notified_events = set() # To prevent duplicate alerts in the current session

    def start(self):
        # 1. Check for reminders every 10 minutes
        self.scheduler.add_job(self.check_reminders, 'interval', minutes=10)
        
        # 2. Daily summary at 8:00 AM
        self.scheduler.add_job(self.send_daily_summary, CronTrigger(hour=8, minute=0))
        
        self.scheduler.start()
        logger.info("Scheduler started.")

    async def get_admin_services(self):
        admin_id = self.db.get_admin_id()
        if not admin_id:
            return None, None
            
        creds = self.auth_service.get_credentials(admin_id)
        if not creds:
            return admin_id, None
            
        return admin_id, GoogleServices(credentials_object=creds)

    async def check_reminders(self):
        logger.info("Checking for reminders...")
        admin_id, services = await self.get_admin_services()
        if not services:
            return

        now = datetime.datetime.now()
        # Look for events in the next 2 hours
        time_min = now.isoformat() + 'Z'
        time_max = (now + datetime.timedelta(hours=2)).isoformat() + 'Z'
        
        events = services.check_availability("primary", time_min, time_max)
        if isinstance(events, str): # Error message
            return

        for event in events:
            event_id = event['id']
            start_str = event['start'].get('dateTime', event['start'].get('date'))
            start_time = datetime.datetime.fromisoformat(start_str.replace('Z', '+00:00')).replace(tzinfo=None)
            
            diff = start_time - now
            minutes_to_start = diff.total_seconds() / 60
            
            description = event.get('description', '')
            
            # --- 1. Customer Reminder (60 mins before) ---
            if 50 <= minutes_to_start <= 70:
                if f"customer_{event_id}" not in self.notified_events:
                    # Extract Telegram ID from description "Ref: [ID]"
                    import re
                    match = re.search(r"Ref: (\d+)", description)
                    if match:
                        customer_id = match.group(1)
                        await self.send_telegram_message(customer_id, 
                            f"⏰ Recordatorio: Tienes una cita en la barbería en 1 hora ({start_time.strftime('%H:%M')}). ¡Te esperamos!")
                        self.notified_events.add(f"customer_{event_id}")

            # --- 2. Admin Alert (15 mins before) ---
            if 10 <= minutes_to_start <= 20:
                if f"admin_{event_id}" not in self.notified_events:
                    await self.send_telegram_message(admin_id, 
                        f"💈 Próximo cliente: En 15 minutos tienes a *{event.get('summary', 'Alguien')}*.")
                    self.notified_events.add(f"admin_{event_id}")

    async def send_daily_summary(self):
        logger.info("Sending daily summary to admin...")
        admin_id, services = await self.get_admin_services()
        if not services:
            return

        now = datetime.datetime.now()
        time_min = now.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
        time_max = now.replace(hour=23, minute=59, second=59).isoformat() + 'Z'
        
        events = services.check_availability("primary", time_min, time_max)
        if isinstance(events, str) or not events:
            message = "📅 Buenos días! Hoy no tienes citas programadas aún."
        else:
            message = "📅 *Agenda de Hoy:*\n\n"
            # Sort events by time
            sorted_events = sorted(events, key=lambda x: x['start'].get('dateTime', ''))
            for e in sorted_events:
                t = e['start'].get('dateTime', '')
                if t:
                    time_str = datetime.datetime.fromisoformat(t.replace('Z', '+00:00')).strftime('%H:%M')
                    message += f"• {time_str} - {e.get('summary', 'Cita')}\n"
            
        await self.send_telegram_message(admin_id, message)

    async def send_telegram_message(self, chat_id, text):
        try:
            await self.bot_app.bot.send_message(chat_id=chat_id, text=text, parse_mode='Markdown')
            logger.info(f"Notification sent to {chat_id}: {text[:30]}...")
        except Exception as e:
            logger.error(f"Error sending notification to {chat_id}: {e}")

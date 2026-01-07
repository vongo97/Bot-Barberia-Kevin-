import os
import datetime
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/spreadsheets'
]

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleServices:
    def __init__(self, credentials_file='credentials.json', credentials_object=None):
        """
        Initializes Google Services.
        - credentials_object: Pre-loaded Credentials object (for SaaS/DB usage).
        - credentials_file: Path to client_secrets (for local desktop flow).
        """
        self.creds = None

        if credentials_object:
            self.creds = credentials_object
        else:
            # Fallback for local testing (token.json file)
            if os.path.exists('token.json'):
                try:
                    self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
                except Exception as e:
                    logger.warning(f"Error loading token.json: {e}")

            # If no valid token, let user log in (Desktop Flow)
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    try:
                        self.creds.refresh(Request())
                    except Exception as e:
                        logger.warning(f"Error refreshing token: {e}")
                        self.creds = None

                if not self.creds and os.path.exists(credentials_file):
                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_file, SCOPES)
                    self.creds = flow.run_local_server(port=0)
                    with open('token.json', 'w') as token:
                        token.write(self.creds.to_json())
        
        if self.creds:
            self.calendar_service = build('calendar', 'v3', credentials=self.creds)
            self.sheets_service = build('sheets', 'v4', credentials=self.creds)
        else:
            self.calendar_service = None
            self.sheets_service = None


    def create_event(self, calendar_id, summary, description, start_time, end_time):
        """
        Creates a Google Calendar event.
        start_time and end_time should be ISO strings.
        """
        if not self.calendar_service: return None
        
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time, 
                'timeZone': 'America/Bogota', # Adjust as needed
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'America/Bogota',
            },
        }

        try:
            event_result = self.calendar_service.events().insert(calendarId=calendar_id, body=event).execute()
            logger.info(f"Event created: {event_result.get('htmlLink')}")
            return event_result
        except HttpError as error:
            logger.error(f"An error occurred in create_event: {error}")
            return None

    def delete_event(self, calendar_id, event_id):
        """Deletes an event by ID."""
        if not self.calendar_service: return None
        try:
            self.calendar_service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
            logger.info(f"Event {event_id} deleted.")
            return True
        except HttpError as error:
            logger.error(f"An error occurred in delete_event: {error}")
            return False

    def update_event(self, calendar_id, event_id, start_time, end_time, summary=None):
        """Updates an event (Reschedule)."""
        if not self.calendar_service: return None
        try:
            # First get the event to keep other fields
            event = self.calendar_service.events().get(calendarId=calendar_id, eventId=event_id).execute()
            
            event['start']['dateTime'] = start_time
            event['end']['dateTime'] = end_time
            if summary:
                event['summary'] = summary
                
            updated_event = self.calendar_service.events().update(calendarId=calendar_id, eventId=event_id, body=event).execute()
            logger.info(f"Event {event_id} updated.")
            return updated_event
        except HttpError as error:
            logger.error(f"An error occurred in update_event: {error}")
            return None

    def check_availability(self, calendar_id, time_min, time_max):
        """
        List events in a time range to check availability.
        time_min and time_max are ISO strings.
        """
        if not self.calendar_service: return []
        try:
            events_result = self.calendar_service.events().list(
                calendarId=calendar_id, timeMin=time_min, timeMax=time_max,
                singleEvents=True, orderBy='startTime'
            ).execute()
            return events_result.get('items', [])
        except HttpError as error:
            logger.error(f"An error occurred in check_availability: {error}")
            return []

    def log_to_sheet(self, spreadsheet_id, range_name, values):
        """
        Appends a row to Google Sheets.
        values: List of values [Nombre, Servicio, Precio, Hora, Estatus, Dia, Celular, ID, ...]
        """
        if not self.sheets_service: return None
        body = {
            'values': [values]
        }
        try:
            result = self.sheets_service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id, range=range_name,
                valueInputOption="USER_ENTERED", body=body
            ).execute()
            logger.info(f"{result.get('updates').get('updatedCells')} cells appended.")
            return result
        except HttpError as error:
            logger.error(f"An error occurred in log_to_sheet: {error}")
            return None

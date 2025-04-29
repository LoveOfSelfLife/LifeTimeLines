import json

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from common.fitness.member_info import get_user_profile
from common.vault import Vault
from datetime import datetime, timedelta

SCOPES = ["https://www.googleapis.com/auth/calendar"]
FITNESS_SECRETS_VAULT = "lifetimelines-secrets-1"
FITNESS_SECRETS_VAULT_TOKEN="activefitnessapp-token"
FITNESS_SECRETS_VALUT_CLIENT_CONFIG="activefitnessapp-client-config"

class GoogleCalendarService:

    def __init__(self):
        self.service = build_calendar_service()
        self.calendar_id = 'primary'

    def get_events(self, date_min:str=None, date_max:str=None):
        """
        Fetches events from the Google Calendar.

        Args:
            date_min (str): The minimum time is in a YYYY-MM-DD format. Defaults to None.
            date_max (str): The maximum time is in a YYYY-MM-DD format. Defaults to None.

        Returns:
            list: A list of events from the specified calendar.
        """
        if date_min:
            date_min = datetime.strptime(date_min, "%Y-%m-%d").date()
            time_min = date_min.isoformat() + 'T00:00:00Z'
        else:
            time_min = None

        if date_max:
            date_max = datetime.strptime(date_max, "%Y-%m-%d").date()
            time_max = date_max.isoformat() + 'T23:59:59Z'
        else:
            time_max = None

        try:
            events_result = self.service.events().list(calendarId=self.calendar_id,  
                                                       timeMin=time_min, timeMax=time_max).execute()
            return events_result.get('items', [])
        except Exception as error:
            print(f"An error occurred: {error}")
            return []
        

    def get_dates_and_events_stream(self, date_min:str=None, date_max:str=None):
        """
        will return a list of json ojbects of two types, date and event
        date objects will starte at date_min and end at date_max
        event objects will be the events in the calendar between date_min and date_max
        
        the date objects will be in the format:
        {
            "type": "date",
            "date": "2025-04-30",
            "month": "April",    
            "monthDay": 30,
            "dayOfWeek": "Wed"
        }

        the event objects will be in the format:
        {
            "id": "1c6ppmviq4tl9q5hc8gbpqmn7s",
            "type": "event",
            "date": "2025-04-28",
            "dayOfWeek": "Mon",
            "month": "April",
            "monthDay": 28,
            "time": "06:00 AM",
            "summary": "workout: james"
        }
                
        the event objects will be populated from the result of the get_events method
        as we iterate thrhough the events, we will create a date object for each sequence of events that have the same date
        and add it to the list of events.  we will also add the subsequent events that have the same date to the list of events
        when the date changes, we will add the date object to the list of events and continue adding events until the date changes again.
        we will continue this process until we reach the end of the date range.

        """
        events = [
            {
                "type": "date",
                "date": "2025-04-26",
                "month": "April",    
                "monthDay": 26,
                "dayOfWeek": "Sat"
            },
            {
                "type": "date",
                "date": "2025-04-27",
                "month": "April",    
                "monthDay": 27,
                "dayOfWeek": "Sun"
            },
            {
                "type": "date",
                "date": "2025-04-28",
                "month": "April",    
                "monthDay": 28,
                "dayOfWeek": "Mon"
            },
            {
            "id": "1c6ppmviq4tl9q5hc8gbpqmn7s",
            "type": "event",
            "date": "2025-04-28",
            "dayOfWeek": "Mon",
            "month": "April",
            "monthDay": 28,
            "time": "06:00 AM",
            "summary": "workout: james"
            },
            {
            "id": "2c6ppmviq4tl9q5hc8gbpqmn7s",
            "type": "event",
            "date": "2025-04-28",
            "dayOfWeek": "Mon",
            "month": "April",    
            "monthDay": 28,
            "time": "07:00 AM",
            "summary": "workout: jocelyn"
            },
        {
            "id": "2c6ppmviq4tl9q5hc8gbpqmn7s2",
            "type": "event",
            "date": "2025-04-28",
            "dayOfWeek": "Mon",
            "month": "April",
            "monthDay": 28,
            "time": "07:00 AM",
            "summary": "workout: rich"
            },
            {
            "id": "2c6ppmviq4tl9q5hc8gbpqmn7s3",
            "type": "event",
            "date": "2025-04-28",
            "dayOfWeek": "Mon",
            "month": "April",
            "monthDay": 28,
            "time": "07:00 AM",
            "summary": "workout: joe p"
            },
            {
                "type": "date",
                "date": "2025-04-29",
                "month": "April",    
                "monthDay": 29,
                "dayOfWeek": "Tue"
            },
            {
            "id": "3c6ppmviq4tl9q5hc8gbpqmn7s",
            "type": "event",
            "date": "2025-04-29",
            "dayOfWeek": "Tue",
            "month": "April",
            "monthDay": 29,
            "time": "06:00 AM",
            "summary": "workout: Stephanie"
            },
            {
            "id": "4c6ppmviq4tl9q5hc8gbpqmn7s",
            "type": "event",
            "date": "2025-04-29",
            "dayOfWeek": "Tue",
            "month": "April",
            "monthDay": 29,
            "time": "07:00 AM",
            "summary": "workout: Kathy"
            },
            {
                "type": "date",
                "date": "2025-04-30",
                "month": "April",    
                "monthDay": 30,
                "dayOfWeek": "Wed"
            },
            {
            "id": "4c6ppmviq4tl9q5hc8gbpqmn7s",
            "type": "event",
            "date": "2025-04-30",
            "dayOfWeek": "Wed",
            "month": "April",
            "monthDay": 30,
            "time": "06:00 AM",
            "summary": "workout: Rich K"
            }        
        ]
        events = self.get_events(date_min=date_min, date_max=date_max)
        sorted_events = sorted(events, key=lambda x: x['start'].get('dateTime', x['start'].get('date')))
        events_list = []
        date_cursor = event_date_dt = datetime.fromisoformat(date_min).date()

        for event in sorted_events:
            event_date_dt = get_date_of_event(event)
            while date_cursor <= event_date_dt:
                # add a date object for the date cursor to the output stream
                date_dict = {
                    "type": "date",
                    "date": date_cursor.strftime("%Y-%m-%d"),
                    "month": date_cursor.strftime("%B"),
                    "monthDay": date_cursor.strftime("%d"),
                    "dayOfWeek": date_cursor.strftime("%a"),
                    "display_date": date_cursor.strftime("%B %d")
                }
                events_list.append(date_dict)
                date_cursor += timedelta(days=1)

            event_date = event['start'].get('dateTime', event['start'].get('date'))
            event_date_dt = datetime.fromisoformat(event_date).date()
            event_time = event['start'].get('dateTime', event['start'].get('date'))
            event_time = datetime.fromisoformat(event_time).time()
            event_display_time = event_time.strftime("%I:%M %p")
            event_time = event_time.strftime("%H:%M")
            event_day_of_week = event_date_dt.strftime("%a")
            event_month = event_date_dt.strftime("%B")
            event_month_day = event_date_dt.strftime("%d")
            event_month_day = int(event_month_day)
            event_date = event_date_dt.strftime("%Y-%m-%d")
            # display date as month name and day of month
            event_display_date = event_date_dt.strftime("%B %d")
            event_summary = event.get('summary', '')
            event_id = event.get('id', '')
            event_type = 'event'
            event_dict = {
                'id': event_id,
                'type': event_type,
                'date': event_date_dt,
                'display_date': event_display_date,
                'dayOfWeek': event_day_of_week,
                'month': event_month,
                'monthDay': event_month_day,
                'time': event_time,
                'display_time': event_display_time,
                'summary': event_summary
            }
            events_list.append(event_dict)
        
        return events_list


    def add_workout_event(self, member_id, event_date, event_time, location='', description='workout session'):
        """
        Adds an event to the Google Calendar.

        Args:
            event (dict): The event to add.
        """
        
        # date is formatted as MM/DD/YYYY
        # time is formatted as HH:MM in military time
        # location is formatted as "YMCA, Cranford, NJ" 
        # convert date & time to ISO 8601 format

        event_date = datetime.strptime(event_date, "%Y-%m-%d").date()
        event_time = datetime.strptime(event_time, "%H:%M").time()
        event_datetime = datetime.combine(event_date, event_time)
        #end time is 1 hour later
        event_datetime_end = event_datetime + timedelta(hours=1)
        profile = get_user_profile(member_id)
        if profile:
            member_short_name = profile.get('short_name', member_id)
        else:
            print(f"Unable to get profile for member id {member_id}")

        event = {
            'summary': f'{member_short_name}',
            'location': location,
            'description': description,
            'start': {
                'dateTime': f'{event_datetime.isoformat()}',
                'timeZone': 'America/New_York'
            },
            'end': {
                'dateTime': f'{event_datetime_end.isoformat()}',
                'timeZone': 'America/New_York', 
            }
        }

        try:
            event = self.service.events().insert(calendarId=self.calendar_id, body=event).execute()
            print("Event created: %s" % (event.get("htmlLink")))
        except Exception as error:
            print(f"An error occurred: {error}")

    def update_workout_event(self, id, event_date, event_time, member_id, location='', description='workout session'):
        print(f"Updating event {id} to {event_date} at {event_time} for member {member_id}")
        """
        Adds an event to the Google Calendar.

        Args:
            event (dict): The event to add.
        """
        
        # date is formatted as MM/DD/YYYY
        # time is formatted as HH:MM in military time

        event_date = datetime.strptime(event_date, "%Y-%m-%d").date()
        event_time = datetime.strptime(event_time, "%H:%M").time()
        event_datetime = datetime.combine(event_date, event_time)
        #end time is 1 hour later
        event_datetime_end = event_datetime + timedelta(hours=1)

        profile = get_user_profile(member_id)
        if profile:
            member_short_name = profile.get('short_name', member_id)
        else:
            print(f"Unable to get profile for member id {member_id}")

        event = {
            'summary': f'{member_short_name}',
            'location': location,
            'description': description,
            'start': {
                'dateTime': f'{event_datetime.isoformat()}',
                'timeZone': 'America/New_York'
            },
            'end': {
                'dateTime': f'{event_datetime_end.isoformat()}',
                'timeZone': 'America/New_York', 
            }
        }

        try:
            event = self.service.events().update(calendarId=self.calendar_id, eventId=id, body=event).execute()
            print("Event created: %s" % (event.get("htmlLink")))
        except Exception as error:
            print(f"An error occurred: {error}")

    def delete_workout_event(self, id):
        try:
            event = self.service.events().delete(calendarId=self.calendar_id, eventId=id).execute()
            print("Event deleted: %s" % (event.get("htmlLink"))) 
        except Exception as error:
            print(f"An error occurred: {error}")



def get_date_of_event(event):
    event_date = event['start'].get('dateTime', event['start'].get('date'))
    event_date = datetime.fromisoformat(event_date).date()
    return event_date

def build_calendar_service():
    """
    Builds the Google Calendar API service.

    Args:
        token_data (str): The token data in JSON format. Defaults to None.

    Returns:
        service: The Google Calendar API service instance.
    """

    vault = Vault(FITNESS_SECRETS_VAULT)
    token_data = vault.get_secret_from_vault(FITNESS_SECRETS_VAULT_TOKEN)

    if token_data:
        token = json.loads(token_data)
        creds = Credentials.from_authorized_user_info(token, SCOPES)
    else:
        print("No token found in vault.")
        creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # originally we did this step from a file
            # flow = InstalledAppFlow.from_client_secrets_file("c:/users/richk/downloads/activefitnessapp_credentials.json", SCOPES)
            # we really shouldn't be getting to this step
            client_config = vault.get_secret_from_vault(FITNESS_SECRETS_VALUT_CLIENT_CONFIG)
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)

    # Save the credentials for the next run
    vault.set_secret_to_vault(FITNESS_SECRETS_VAULT_TOKEN, creds.to_json())

    # Build the service
    service = build("calendar", "v3", credentials=creds)
    return service

def get_google_calendar_events(service, calendar_id='primary', time_min=None, time_max=None):
    """
    Fetches events from a Google Calendar.

    Args:
        service: The Google Calendar API service instance.
        calendar_id (str): The ID of the calendar to fetch events from. Defaults to 'primary'.
        time_min (str): The minimum time in RFC3339 format. Defaults to None.
        time_max (str): The maximum time in RFC3339 format. Defaults to None.

    Returns:
        list: A list of events from the specified calendar.
    """
    events_result = service.events().list(calendarId=calendar_id, timeMin=time_min, timeMax=time_max).execute()
    return events_result.get('items', [])


    # event = {
    #     'summary': 'Google I/O 2015',
    #     'location': '800 Howard St., San Francisco, CA 94103',
    #     'description': 'A chance to hear more about Google\'s developer products.',
    #     'start': {
    #         'dateTime': '2025-05-28T09:00:00-07:00',
    #         'timeZone': 'America/Los_Angeles',
    #     },
    #     'end': {
    #         'dateTime': '2025-05-28T17:00:00-07:00',
    #         'timeZone': 'America/Los_Angeles',
    #     },
    #     'recurrence': [
    #         'RRULE:FREQ=DAILY;COUNT=2'
    #     ],
    #     'attendees': [
    #         {'email': 'lpage@example.com'},
    #         {'email': 'sbrin@example.com'},
    #     ],
    #     'reminders': {
    #         'useDefault': False,
    #         'overrides': [
    #         {'method': 'email', 'minutes': 24 * 60},
    #         {'method': 'popup', 'minutes': 10},
    #         ],
    #     },
    # }



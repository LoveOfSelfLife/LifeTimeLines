from common.fitness.google_calendar_events import GoogleCalendarService

calendar_service = None 
def get_calendar_service():
    global calendar_service
    if calendar_service is None:
        calendar_service = GoogleCalendarService()
    return calendar_service
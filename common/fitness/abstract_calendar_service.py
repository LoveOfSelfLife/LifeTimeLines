class AbstractCalendarService:

    def get_dates_and_events_stream(self, date_min:str, date_max:str, filter_by_member_id_func):
        raise NotImplementedError("Subclasses must implement this method")

    def add_workout_event(self, member_short_name: str, event_date: str, event_time: str, location: str, metadata: str):
        raise NotImplementedError("Subclasses must implement this method")

    def add_recurring_workout_event(self, member_short_name: str, event_date: str, event_time: str, frequency: str, byday: str, location: str, metadata: str):
        raise NotImplementedError("Subclasses must implement this method")

    def get_event(self, event_id: str):
        raise NotImplementedError("Subclasses must implement this method")

    def get_recurring_workout_event_details(self, recurring_event_id: str):
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_events(self, member_short_name: str):
        raise NotImplementedError("Subclasses must implement this method")
    
    def update_workout_event(self, event_id: str, updated_fields: dict):
        raise NotImplementedError("Subclasses must implement this method")

    def update_recurring_workout_event(self, recurring_event_id: str, member_short_name: str, event_date: str, event_time: str, frequency: str, byday: str, location: str, metadata: str):
        raise NotImplementedError("Subclasses must implement this method")
    
    def delete_workout_event(self, event_id: str):
        raise NotImplementedError("Subclasses must implement this method")

    def delete_recurring_workout_event(self, recurring_event_id: str):
        raise NotImplementedError("Subclasses must implement this method")
    
    
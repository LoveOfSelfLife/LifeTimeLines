from datetime import datetime
import json
import os

from common.blob_store import BlobStore
from common.entity_store import EntityObject, EntityStore
from common.fitness.members import MemberEntity
from common.fitness.utils import generate_id

class EventEntity (EntityObject):
    PARTITION_VALUE = "fitness"
    table_name="EventTable"
    fields=["event_id", "type", "datetime", "name", "description", "location"]
    key_field="event_id"
    partition_value=PARTITION_VALUE

    def __init__(self, d={}):
        super().__init__(d)

class JoinedEntity (EntityObject):
    table_name="JoinedTable"
    fields=["joined_id", "event_id", "member_id", "activity_id"]
    key_field="joined_id"
    partition_field="event_id"
    
    def __init__(self, d={}):
        super().__init__(d)

class ActivityEntity (EntityObject):
    table_name="ActivityTable"
    fields=["activity_id", "member_id", "activity_name", "program_instance"]
    key_field="activity_id"
    partition_value = "activity"
    
    def __init__(self, d={}):
        super().__init__(d)

def day_of_week_to_string(datetime_dt):
    day_of_week = datetime_dt.isoweekday()
    return ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"][day_of_week]


def list_events(logged_in_member_id, from_date, to_date):
    es = EntityStore()
    events = []
    for e in es.list_items(EventEntity()):
        event = {}
        event["event_id"] = e["event_id"]
        dt = datetime.fromisoformat(e["datetime"])
        event["datetime_dt"] = dt
        event["day_of_week"] = day_of_week_to_string(dt)
        event["date"] = dt.strftime("%b-%d-%Y")
        event["time"] = dt.strftime("%I:%M %p")
        event["name"] = e["name"]
        event["description"] = e["description"]
        event["location"] = e["location"]
        events.append(event)

    # find out who has joined each event    
    for event in events:
        event["joined"] = []
        joined = es.list_items(JoinedEntity({ "event_id": event["event_id"]}))
        for j in joined:
            member_id = j.get("member_id", None)
            if member_id is None:
                continue
            details = {}
            details["event"] = event
            details["member_id"] = member_id
            mbr = es.get_item(MemberEntity({ "id": member_id }))
            details["member_short_name"] = mbr["short_name"]

            activity_id = j.get("activity_id", None)
            # TODO:  fix this hack with the "null" string
            if activity_id and activity_id != "null":
                details["activity_id"] = j["activity_id"]
                activity = es.get_item(ActivityEntity({ "activity_id": activity_id }))
                details["activity_name"] = activity["activity_name"]
            else:
                details["activity_id"] = ""
                details["activity_name"] = "No activity yet"
            event["joined"].append(details)
            if logged_in_member_id == member_id:
                event["member_joined_details"] = details
    return events

def get_event(event_id):
    es = EntityStore()
    event = es.get_item(EventEntity({ "event_id": event_id }))
    return event

def create_event(_event_def):
    es = EntityStore()
    id = generate_id("ev")
    _event_def["event_id"] = id
    event = EventEntity(_event_def)
    es.upsert_item(event)
    return event

def update_event(_event_def):
    print("update_event - not implemented")
    pass

def create_activity(_activity_def):
    es = EntityStore()
    id = generate_id("at")
    _activity_def["activity_id"] = id
    activity = ActivityEntity(_activity_def)
    es.upsert_item(activity)
    return activity

def list_activities():
    es = EntityStore()
    activities = []
    for e in es.list_items(ActivityEntity()):
        activity = {}
        activity["activity_id"] = e["activity_id"]
        activity["activity_name"] = e["activity_name"]
        activity["program_instance"] = e["program_instance"]
        activities.append(activity)
    return activities

def get_activity(activity_id):
    es = EntityStore()
    activity = es.get_item(ActivityEntity({ "activity_id": activity_id }))
    return activity

def create_joined_entity(_joined_def):
    es = EntityStore()
    id = generate_id("jn")
    _joined_def["joined_id"] = id
    joined = JoinedEntity(_joined_def)
    es.upsert_item(joined)
    return joined

def list_joined_entities():
    es = EntityStore()
    joined_entities = []
    for e in es.list_items(JoinedEntity()):
        joined_entity = {}
        joined_entity["joined_id"] = e["joined_id"] 
        joined_entity["event_id"] = e["event_id"]
        joined_entity["member_id"] = e["member_id"]
        joined_entity["activity_id"] = e["activity_id"]
        joined_entities.append(joined_entity)
    return joined_entities

def get_joined_entity(joined_id):
    es = EntityStore()
    joined_entity = es.get_item(JoinedEntity({ "joined_id": joined_id }))
    return joined_entity

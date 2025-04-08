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
    fields=["event_id", "type", "datetime", "name", "description", "location", "owner_member_id", "joined"]
    key_field="event_id"
    partition_value=PARTITION_VALUE

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


def map_event(e):
    event = {}
    if "event_id" in e:
        event["event_id"] = e["event_id"]
    dt = datetime.fromisoformat(e["datetime"])
    event["datetime_dt"] = dt
    event["day_of_week"] = day_of_week_to_string(dt)
    event["date"] = dt.strftime("%Y-%m-%d")
    event["time"] = dt.strftime("%H:%M")
    event["time_display"] = dt.strftime("%I:%M %p")
    event["month"] = dt.strftime("%b")
    event["month_day"] = dt.strftime("%d")
    event["name"] = e.get("name", "")
    event["type"] = e.get("type", "")
    event["description"] = e.get("description", "")
    event["location"] = e.get("location", "")
    event["joined"] = e.get("joined", [])
    return event

def list_events(logged_in_member_id, from_date, to_date):
    es = EntityStore()
    events = []
    
    for e in es.list_items(EventEntity()):
        event = map_event(e)
        is_joined = False
        joined_list = []
        my_activity = ""
        for j in event.get("joined", []):
            mbr = es.get_item(MemberEntity({ "id": j["member_id"] }))
            j["member_short_name"] = mbr["short_name"]
            if j["member_id"] == logged_in_member_id:
                my_activity = j["activity"]
                is_joined = True
            joined_list.append(j)
        event["is_joined"] = is_joined
        event["joined"] = joined_list
        event["my_activity"] = my_activity
        event["num_members_joined"] = len(event["joined"])
        if e.get("owner_member_id") == logged_in_member_id:
            event["is_owner"] = True
        else:
            event["is_owner"] = False
        events.append(event)
    return events

def get_event(event_id):
    es = EntityStore()
    event = es.get_item(EventEntity({ "event_id": event_id }))
    if event:
        event = map_event(event)
    return event

def create_new_event(member_id):
    event = EventEntity()
    event["type"] = "e"
    event["name"] = ""
    event["description"] = ""
    event["location"] = "Cranford YMCA"
    event["datetime"] = ""
    event["ownder_member_id"] = member_id
    event["joined"] = []
    return event

def create_event(_event_def):
    es = EntityStore()
    id = generate_id("ev")
    _event_def["event_id"] = id
    event = EventEntity(_event_def)
    es.upsert_item(event)
    return event

def store_event(event_def):
    es = EntityStore()
    event_def["event_id"] = event_def.get("event_id", generate_id("ev"))
    event = EventEntity(event_def)
    es.upsert_item(event)
    return event

def update_event(_event_def):
    print("update_event - not implemented")
    pass

def delete_event(event_id):
    es = EntityStore()
    es.delete([event_id],EventEntity)
    
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

from datetime import datetime
import json
import os

from common.blob_store import BlobStore
from common.entity_store import EntityObject, EntityStore
from common.fitness.member_entity import MemberEntity
from common.fitness.utils import generate_id
from common.fitness.message_publisher import MessagePublisher

class EventTypes:
    EVENT_CREATED = "event_created"
    EVENT_UPDATED = "event_updated"
    EVENT_DELETED = "event_deleted"
    EVENT_MEMBER_JOINED = "event_member_joined"
    EVENT_MEMBER_LEFT = "event_member_left"
    EVENT_MEMBER_ACTIVITY = "event_member_activity"
    EVENT_MEMBER_ACTIVITY_UPDATED = "event_member_activity_updated"
    EVENT_MEMBER_ACTIVITY_DELETED = "event_member_activity_deleted"
    

class WorkoutSessionEntity (EntityObject):
    PARTITION_VALUE = "fitness"
    table_name="WorkoutSessionTable"
    fields=["id", "type", "datetime", "name", "description", "location", "owner_member_id", "joined"]
    key_field="id"
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


def map_workout_session(e):
    workout_session = {}
    if "id" in e:
        workout_session["id"] = e["id"]
    dt = datetime.fromisoformat(e["datetime"])
    workout_session["datetime"] = e["datetime"]
    workout_session["day_of_week"] = day_of_week_to_string(dt)
    workout_session["date"] = dt.strftime("%Y-%m-%d")
    workout_session["time"] = dt.strftime("%H:%M")
    workout_session["time_display"] = dt.strftime("%I:%M %p")
    workout_session["month"] = dt.strftime("%b")
    workout_session["month_day"] = dt.strftime("%d")
    workout_session["name"] = e.get("name", "")
    workout_session["type"] = e.get("type", "")
    workout_session["description"] = e.get("description", "")
    workout_session["location"] = e.get("location", "")
    workout_session["joined"] = e.get("joined", [])
    return workout_session

def list_workout_sessions(logged_in_member_id, from_date, to_date):
    es = EntityStore()
    workout_sessions = []
    
    for e in es.list_items(WorkoutSessionEntity()):
        workout_session = map_workout_session(e)
        # check if event is in the date range
        if datetime.fromisoformat(workout_session["datetime"]) < datetime.fromisoformat(from_date) or  \
           datetime.fromisoformat(workout_session["datetime"]) > datetime.fromisoformat(to_date):
            continue
        is_joined = False
        joined_list = []
        my_activity = ""
        for j in workout_session.get("joined", []):
            mbr = es.get_item(MemberEntity({ "id": j["member_id"] }))
            j["member_short_name"] = mbr["short_name"]
            if j["member_id"] == logged_in_member_id:
                my_activity = j["activity"]
                is_joined = True
            joined_list.append(j)
        workout_session["is_joined"] = is_joined
        workout_session["joined"] = joined_list
        workout_session["my_activity"] = my_activity
        workout_session["num_members_joined"] = len(workout_session["joined"])
        if e.get("owner_member_id") == logged_in_member_id:
            workout_session["is_owner"] = True
        else:
            workout_session["is_owner"] = False
        workout_sessions.append(workout_session)
    return workout_sessions

def get_workout_session(id):
    es = EntityStore()
    workout_session = es.get_item(WorkoutSessionEntity({ "id": id }))
    if workout_session:
        workout_session = map_workout_session(workout_session)
    return workout_session

def create_new_workout_session(member_id):
    workout_session = WorkoutSessionEntity()
    workout_session["type"] = "e"
    workout_session["name"] = ""
    workout_session["description"] = ""
    workout_session["location"] = "Cranford YMCA"
    workout_session["datetime"] = ""
    workout_session["ownder_member_id"] = member_id
    workout_session["joined"] = []
    return workout_session

def store_workout_session(update_type, workout_session_def):
    es = EntityStore()
    workout_session_def["id"] = workout_session_def.get("id", generate_id("ev"))
    workout_session = WorkoutSessionEntity(workout_session_def)
    es.upsert_item(workout_session)
    ep = MessagePublisher()
    ep.publish_message(update_type, workout_session)

    return workout_session

def delete_workout_session(id):
    es = EntityStore()
    es.delete([id],WorkoutSessionEntity)
    
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

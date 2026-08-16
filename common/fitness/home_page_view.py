import json

import pytz
from common.entity_store import EntityStore
from common.fitness.hx_common import hx_render_template
from common.fitness.programs import get_members_current_active_program, get_next_workout_in_program
from common.fitness.member_workout_entity import MemberWorkoutInstanceEntity, get_exercises_from_workout
from common.fitness.workout_state import get_active_workout_state
from common.fitness.workouts import get_scheduled_workouts
from datetime import datetime, timedelta, timezone
from flask import render_template, render_template_string, request, redirect, session, url_for
from common.fitness.hx_common import rm_spaces
from common.fitness.get_calendar_service import get_calendar_service


def to_datetime_local_value(timestamp):
    if not timestamp:
        return ""

    try:
        return datetime.fromisoformat(str(timestamp).replace('Z', '+00:00')).strftime('%Y-%m-%dT%H:%M')
    except ValueError:
        return ""

def format_seconds(N: int) -> str:
    if N < 0:
        return "about now"
    days, rem   = divmod(N, 86400)
    hours, rem  = divmod(rem, 3600)
    minutes     = rem // 60

    parts = []
    if days:
        parts.append(f"{int(days)} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{int(hours)} hour{'s' if hours != 1 else ''}")
    parts.append(f"{int(minutes)} minute{'s' if minutes != 1 else ''}")

    if len(parts) > 1:
        return ", ".join(parts[:-1]) + " and " + parts[-1] + " from now"
    return parts[0] + " from now"

def render_home_page_workout(member, current_state):

    # render the workout that is in progress
    workout_instance_key = current_state.get('workout_instance_key', None)
    program_key = current_state.get('program_key', None)
    workout_started_ts = current_state.get('time_workout_started', None)

    program_composite_key = eval(program_key) if program_key else None
    scheduled_workout_event_id = current_state.get('scheduled_workout_event_id', None)
    es = EntityStore()
    workout_instance = es.get_item_by_composite_key(workout_instance_key)
    if not workout_instance:
        # The workout instance is not found, so we display an error message
        return render_template_string('<h1>Workout in progress not found</h1>')
    program_entity = es.get_item_by_composite_key(program_composite_key)

    # The member has a workout in progress
    wrkout_exercises = get_exercises_from_workout(workout_instance)
    exercises = { ex.get('id', None): ex for ex in wrkout_exercises }
    workout_sections = workout_instance.get('workout_sections', [])

    # only use the session value if it exists
    last = session.get(f"last_section_{workout_instance['id']}")  # no fallback
    workout_view_preference = session.get('workout_view_preference', 'accordion')
    # if last section is not set, then we set the last section to be the first section of the workout that has more than one exercise in it
    if not last:
        for section in workout_sections:
            if len(section.get('exercises', [])) > 0:
                last = section.get('name', None)
                break
        
    return hx_render_template(
        "workout_view.html",
        workout=workout_instance,
        workout_sections=workout_sections,
        exercises=exercises,
        current_parameters=current_state.get('exercise_parameters', {}),
        default_section=last,
        program=program_entity,
        program_key=program_composite_key,
        workout_instance_key=workout_instance_key,
        scheduled_workout_event_id=scheduled_workout_event_id,
        finish_workout_url=url_for('program.finish_workout', 
                                workout_instance_key=workout_instance_key),
        cancel_workout_url=url_for('program.cancel_workout',
                                workout_instance_key=workout_instance_key),
        adjustments=current_state.get('adjustments', {}),
        show_finish_button=True,
        active_workout=True,
        time_workout_started=workout_started_ts,
        workout_view_preference=workout_view_preference,
        rs=rm_spaces
    )

def render_finishing_workout_page(member, current_state):
    workout_instance_key = current_state.get('workout_instance_key', None)
    program_key = current_state.get('program_key', None)
    workout_started_ts = current_state.get('time_workout_started', None)

    # only run eval if program_key is not None and is a string, otherwise set it to program_key
    program_composite_key = eval(program_key) if program_key and isinstance(program_key, str) else None
    scheduled_workout_event_id = current_state.get('scheduled_workout_event_id', None)
    es = EntityStore()
    workout_instance = es.get_item_by_composite_key(workout_instance_key)
    if not workout_instance:
        # The workout instance is not found, so we display an error message
        return render_template_string('<h1>Workout in progress not found</h1>')
    program_entity = es.get_item_by_composite_key(program_composite_key) if program_composite_key else None

    # The member has a workout in progress
    wrkout_exercises = get_exercises_from_workout(workout_instance)
    exercises = { ex.get('id', None): ex for ex in wrkout_exercises }
    workout_sections = workout_instance.get('workout_sections', [])

    # only use the session value if it exists
    last = session.get(f"last_section_{workout_instance['id']}")  # no fallback

    # if last section is not set, then we set the last section to be the first section of the workout that has more than one exercise in it
    if not last:
        for section in workout_sections:
            if len(section.get('exercises', [])) > 0:
                last = section.get('name', None)
                break
    started_ts_local = to_datetime_local_value(workout_started_ts or workout_instance.get('started_ts'))
    local_time_now = datetime.now(timezone.utc).astimezone(pytz.timezone('US/Eastern')).isoformat()
    fininshed_ts_local = to_datetime_local_value(workout_instance.get('finished_ts') or local_time_now)

    exercise_parameters = current_state.get('exercise_parameters', {})
    parameters_changed = len(exercise_parameters) > 0
    return hx_render_template(
        "home/finishing_workout.html",
        workout=workout_instance,
        workout_sections=workout_sections,
        exercises=exercises,
        current_parameters=exercise_parameters,
        parameters_changed=parameters_changed,
        default_section=last,
        program=program_entity,
        program_key=program_composite_key,
        workout_instance_key=workout_instance_key,
        scheduled_workout_event_id=scheduled_workout_event_id,
        workout_started_ts=workout_started_ts,
        workout_started_ts_local=started_ts_local,
        workout_finished_ts_local=fininshed_ts_local,
        workout_feedback=workout_instance.get('member_feedback', ''),
        really_finish_workout_url=url_for('program.really_finish_workout', 
                                workout_instance_key=workout_instance_key),
        continue_workout_url=url_for('program.continue_workout',
                                workout_instance_key=workout_instance_key),
        adjustments=current_state.get('adjustments', {}),
        show_finish_button=False,
        active_workout=False,
        purpose_of_parameter_edit='finishing_workout_next_time',
        workout_definition_key=None,
        rs=rm_spaces
    )

def get_next_workout_event(events, member_id):
    for event in events:
        event_member_id = event.get('member_id', None)
        if member_id == event_member_id:
            event_status = event.get('event_status', '')
            if event_status in ['cancelled', 'done']:
                continue
            workout_dt = event["start"]["dateTime"]
            # calculate how many dates and hours until the workout
            workout_datetime = datetime.fromisoformat(workout_dt.replace('Z', '+00:00'))  # Parse with timezone info
            # here we are only interested in upcoming workouts, so if the workout datetime is in the past, we skip it
            # however, if the workout time was say set to 6:01 AM and it is now 6:30 AM, we still want to consider that workout as upcoming
            # we should consider a workout as upcoming if it is within 1 hour in the past, or anytime in the future

            now = datetime.now(timezone.utc) # Make 'now' timezone-aware
            time_until_workout = (workout_datetime - now).total_seconds()
            if time_until_workout < -3600:  # 1 hour in the past
                continue

            # we found the first event that is for this member
            return event, workout_datetime, time_until_workout
    return None, None, None

def get_workout_intstances_for_program(member_id, program_id):

    workouts = []
    es = EntityStore()
    workout_instances = es.list_items(MemberWorkoutInstanceEntity({"member_id": member_id}))    
    # TODO:  analyze if the cache is an eligible option
    mbr_workout_instances = list(es.list_items(MemberWorkoutInstanceEntity({"member_id": member_id})))
    # workout_instances = [w for w in mbr_workout_instances if w.get('member_program_id', None)==program_id]    

    if not workout_instances:
        return []
    workout_instances = sorted(workout_instances, key=lambda x: x.get('started_ts', ''), reverse=True)  # Sort by started_ts
    for wi in workout_instances:

        st = wi.get('started_ts' , None)
        if st:
            # format the time to this:
            # Mon - Mar 1 at 12:00 PM
            # Convert the ISO format string to a datetime object
            started_when = datetime.fromisoformat(st.replace('Z', '+00:00'))  # Parse with timezone info
            started_when = started_when.strftime('%a - %b %d at %I:%M %p')
        else:
            started_when = 'unknown'

        workouts.append({
            'name': wi.get('name', 'Unknown Workout'),
            'date': started_when,
            'program_name': wi.get('member_program_name', ''),
            'workout_instance_key': wi.get_composite_key()
        })
    return workouts

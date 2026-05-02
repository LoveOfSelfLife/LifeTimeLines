import json
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
    if 'workout_sections' in workout_instance:
        workout_sections = workout_instance.get('workout_sections', [])
    else:
        workout_sections = workout_instance.get('sections', [])             

    # only use the session value if it exists
    last = session.get(f"last_section_{workout_instance['id']}")  # no fallback

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
        rs=rm_spaces
    )

def generate_current_home_page_view(member):
    """
    Generates the current home page view based on the situation of the member.
    The member may or may note have a program that applies to the current date.
    If the member does not hae a program, then we return content that reflects the member's "no-program" situation.
    However, even though the member doesn't have a current program, the member may have an upcoming workout scheduled, 
    in which case we should display that the member needs to get a new program for that workout.

    If on the other hand, the member does have a program, then we can use the program to determine what to display, as follows:
    1. if the member does not have an upcoming workout scheduled, then we display a message:
        "you do not have any upcoming workouts scheduled"
    2. if the member has an upcoming workout scheduled on their calendar, then we display:
        "you have an upcoming workout scheduled in N days & M hours, along with the workout that they would do on that day"
    3. if the member has an upcoming workout scheduled and is within 1 hour of that workout, then we display:
        "you have an upcoming workout scheduled in less than 1 hour, along with the workout that they would do on that day, and a button
        that allows the member to start the workout", at which point the page would display the workout to the member."
    4. if the member has a workout that has stated, then we display the workout that they started. that view will also have a button that 
       allows the member to cancel, pause, resume, or finish the workout.

    current_state = {
        'state': 'workout_started',
        'workout_instance_key': workout_instance_key,
        'program_key': program_composite_key,
        'scheduled_workout_event_id': scheduled_workout_event_id
    }

    """
    current_state = get_active_workout_state()
    if current_state:
        if current_state.get('state', None) == 'workout_started':
            # render the workout that is in progress
            workout_instance_key = current_state.get('workout_instance_key', None)
            program_key = current_state.get('program_key', None)
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
            if 'workout_sections' in workout_instance:
                workout_sections = workout_instance.get('workout_sections', [])
            else:
                workout_sections = workout_instance.get('sections', [])             

            # only use the session value if it exists
            last = session.get(f"last_section_{workout_instance['id']}")  # no fallback
            # if last section is not set, then we set the last section to be the first section of the workout that has more than one exercise in it
            if not last:
                for section in workout_sections:
                    if len(section.get('exercises', [])) > 0:
                        last = section.get('name', None)
                        break
            return render_template(
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
                rs=rm_spaces
            )

    
    HOUR_IN_SECONDS = 3600  # 1 hour in seconds
    cal = get_calendar_service()
    today = datetime.now(timezone.utc)  # Make 'today' timezone-aware
    start_date = today.strftime("%Y-%m-%d")
    end_date = (today + timedelta(days=14)).strftime("%Y-%m-%d")    
    _, sorted_events = cal.get_dates_and_events_stream(date_min=start_date, date_max=end_date)
    member_id = member.get('id', None)
    event = None
    if sorted_events:
        event, workout_datetime, time_until_workout = get_next_workout_event(sorted_events, member_id)
    
    # get this member current active program
    # and find the next workout in this member's program
    current_program = get_members_current_active_program(member_id, current_date_dt=datetime.now())
    if not current_program:
        # The member does not have a program, so we display the no-program message
        return render_template("no_program_assigned.html", member=member)
    
    current_program_key = current_program.get_composite_key()
    next_workout = get_next_workout_in_program(current_program, member_id)
    next_workout_key = next_workout.get('next_workout_key', None)
    last_program_workout_instance_key = next_workout.get('last_workout_instance_key', None)
    adjustments_for_next_workout = next_workout.get('adjustments_for_next_workout', {})
    if next_workout_key is None:
        return render_template("no_program_assigned.html", member=member)
    
    # completed_workouts = [
    #     {'name': 'Workout 1', 'date': '2023-10-01'},
    #     {'name': 'Workout 2', 'date': '2023-10-05'},
    #     {'name': 'Workout 3', 'date': '2023-10-10'}
    # ]
    completed_workouts = get_workout_intstances_for_program(member_id, current_program.get('id', None))
    if event:
        # The member has an upcoming workout scheduled
        return render_template("upcoming_workout.html", 
                                program_name=current_program.get('name', 'No Program Assigned'),
                                next_workout_datetime=workout_datetime,
                                last_program_workout_instance_key=last_program_workout_instance_key,
                                adjustments_for_next_workout=adjustments_for_next_workout,
                                member=member, 
                                workout=next_workout_key,
                                time_until=format_seconds(time_until_workout), 
                                workout_key=next_workout_key,
                                scheduled_workout_event_id=event.get('id', None),
                                program_key=current_program_key,
                                event=event,
                                completed_workouts=completed_workouts)
    else:
        return render_template("no_workouts_scheduled.html", 
                               member=member, 
                               program_key=current_program_key, 
                               workout_key=next_workout_key, 
                               last_program_workout_instance_key=last_program_workout_instance_key,
                               adjustments_for_next_workout=adjustments_for_next_workout)

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

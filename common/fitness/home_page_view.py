from common.fitness.hx_common import hx_render_template
from common.fitness.programs import get_members_program, get_next_workout_in_program
from common.fitness.workouts import get_scheduled_workouts
from datetime import datetime, timedelta, timezone
from flask import render_template_string, request, redirect, url_for

from services.fitnessclub.views.schedule.routes import get_calendar_service

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
    """
    # For now, we just return a simple welcome message
    HOUR_IN_SECONDS = 3600  # 1 hour in seconds
    cal = get_calendar_service()
    today = datetime.now(timezone.utc)  # Make 'today' timezone-aware
    start_date = today.strftime("%Y-%m-%d")
    end_date = (today + timedelta(days=14)).strftime("%Y-%m-%d")    
    _, sorted_events = cal.get_dates_and_events_stream(date_min=start_date, date_max=end_date)
    member_short_name = member.get('short_name', 'Member')
    if sorted_events:
        # find the first event in the list where the 'summary' contains the mmember's short_name
        for event in sorted_events:
            if member_short_name in event['summary']:
                # we found the first event that matches the member's short name
                # we can display the event details
                workout_dt = event["start"]["dateTime"]
                # calculate how many dates and hours until the workout
                workout_datetime = datetime.fromisoformat(workout_dt.replace('Z', '+00:00'))  # Parse with timezone info
                now = datetime.now(timezone.utc) # Make 'now' timezone-aware
                time_until_workout = (workout_datetime - now).total_seconds()
                if time_until_workout < 0:
                    continue
                if time_until_workout < HOUR_IN_SECONDS:
                    # The member has an upcoming workout scheduled in less than an hour
                    return render_template_string(
                        f'<h2>you have an upcoming workout scheduled in less than 1 hour</h2>'
                        f'<p>Workout: {event["summary"]}</p>'
                        f'<button onclick="location.href=\'/start_workout\'">Start Workout</button>'
                    )
                else:
                    # The member has an upcoming workout scheduled in more than an hour
                    days_until_workout = time_until_workout // (24 * 3600)
                    hours_until_workout = (time_until_workout % (24 * 3600)) // 3600
                    return render_template_string(
                        f'<h2>you have an upcoming workout scheduled in {int(days_until_workout)} days and {int(hours_until_workout)} hours</h2>'
                        f'<p>Workout: {event["summary"]}</p>'
                    )
        # If we reach here, it means we did not find any events that match the member's short name

    # If there are no events, we display a message that the member does not have any upcoming workouts scheduled
    return render_template_string(f'<h1>{member["name"]} you do not have any upcoming workouts scheduled</h1>' )

    # first check if the member has started a workout and it is in still in progress
    # if the member has a workout that is in progress, then we display that workout
    # retrieve the workut from redis
    redis_client = current_app.config['SESSION_CACHELIB']
    current_workout = redis_client.get('current_workout')
    if current_workout:
        w = json.loads(current_workout)

    # otherwise, we do the other checks
    current_program = get_members_program(member.get('id', None), current_date=datetime.now())
    if not current_program:
        # The member does not have a program, so we display the no-program message
        return hx_render_template( template_string='<h1>You do not have a program assigned</h1>')

    list_of_scheduled_workout_sessions = get_scheduled_workout_sessions(member.get('id', None), date=datetime.now())
    if not list_of_scheduled_workout_sessions:
        hx_render_template(
            template_string='<h1>You do not have any upcoming workouts scheduled</h1>')
    else:
        # calc time untile the next workout
        next_workout_session = list_of_scheduled_workout_sessions[0]
        seconds_until_next_workout = calc_time_until_workout_session(next_workout_session, datetime.now())
        if time_until_next_workout < HOUR_IN_SECONDS:
            # The member has an upcoming workout scheduled in less than an hour
            return hx_render_template(
                template_string='<h1>You have an upcoming workout scheduled in less than 1 hour</h1>')


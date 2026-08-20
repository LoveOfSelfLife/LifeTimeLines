"""
Home Page Data Service for Active Friends Club (AFC)

Provides data aggregation for the three main home page sections:
1. Scheduled Workouts - upcoming workouts based on member's schedule and program
2. Completed Workouts - recent workout history 
3. Analytics - workout performance reports and summaries

This service combines schedule data, program data, and workout history to create
a comprehensive view for the member's home page dashboard.
"""

from datetime import datetime, timedelta, timezone

import pytz
from common.entity_store import EntityStore
from common.fitness.coach_team_entity import get_team_coaches
from common.fitness.member_entity import get_member_name_from_member_id
from common.fitness.member_team_entity import get_members_team_members, get_team_members
from common.fitness.programs import get_members_current_active_program, get_next_workout_in_program
from common.fitness.member_workout_entity import MemberWorkoutDefinitionEntity, MemberWorkoutInstanceEntity
from common.fitness.get_calendar_service import get_calendar_service
from common.fitness.roles_service import get_current_team_context
from common.fitness.workouts import get_scheduled_workouts
from typing import Dict, List, Optional, Tuple


def format_seconds(N: int) -> str:
    """Format seconds into human readable time string"""
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


def _is_completed_status(status: str) -> bool:
    normalized = (status or '').strip().lower()
    return normalized in ('done', 'completed')


def _event_datetime(event_record: Dict, local_tz) -> datetime:
    event_date = event_record.get('date')
    if isinstance(event_date, str):
        event_date = datetime.fromisoformat(event_date).date()
    event_time_str = event_record.get('time', '00:00')
    try:
        event_time = datetime.strptime(event_time_str, "%H:%M").time()
    except ValueError:
        event_time = datetime.strptime(event_time_str, "%I:%M %p").time()
    return local_tz.localize(datetime.combine(event_date, event_time))


def get_program_workout_options(program) -> List[Dict]:
    """Build the {key, name, description} option list used by workout-selection dropdowns."""
    from common.fitness.programs import get_program_workouts
    options = []
    if not program:
        return options
    for workout_def in get_program_workouts(program):
        options.append({
            'key': str(workout_def.get_composite_key()),
            'name': workout_def.get('name', 'Unnamed Workout'),
            'description': workout_def.get('description', '')
        })
    return options


class HomePageDataService:
    """Service for aggregating all home page data"""
    
    def __init__(self):
        self.entity_store = EntityStore()

    def _fetch_team_events(self, member_id: str, current_datetime: datetime, start_date: str = None, end_date: str = None):
        """
        Single shared calendar fetch: queries team-wide calendar events once and returns them
        parsed/grouped so callers (scheduled workouts, attendance panel) never issue their own
        separate calendar query.

        Returns:
            (events_by_date, member_events, today_date, local_tz, current_member_id_str)
        """
        current_team = get_current_team_context(member_id)
        team_members = get_team_members(current_team['id'])
        team_coaches = get_team_coaches(current_team['id'])
        all_members_of_team = [str(tm.get('member_id')) for tm in team_members] + [str(tc.get('coach_id')) for tc in team_coaches]
        current_member_id_str = str(member_id)
        team_member_filter_func = lambda m_id: str(m_id) in all_members_of_team

        cal = get_calendar_service()
        # Only query around the active dashboard horizon: today + near future.
        # This avoids scanning months of calendar history on each dashboard load.
        if start_date is None:
            start_date = (current_datetime - timedelta(days=1)).strftime("%Y-%m-%d")
        if end_date is None:
            end_date = (current_datetime + timedelta(days=10)).strftime("%Y-%m-%d")
        scheduled_calendar_events, _ = cal.get_dates_and_events_stream(
            date_min=start_date,
            date_max=end_date,
            filter_by_member_id_func=team_member_filter_func,
        )

        local_tz = pytz.timezone('US/Eastern')
        if current_datetime.tzinfo is None:
            current_datetime_local = local_tz.localize(current_datetime)
        else:
            current_datetime_local = current_datetime.astimezone(local_tz)
        today_date = current_datetime_local.date()

        events_by_date = {}
        member_events = []
        for rec in scheduled_calendar_events:
            if rec.get('type') != 'event':
                continue

            scheduled_member_id = rec.get('member_id')
            if not scheduled_member_id:
                continue
            scheduled_member_id_str = str(scheduled_member_id)

            event_dt = _event_datetime(rec, local_tz)
            event_row = {
                'member_id': scheduled_member_id_str,
                'event_datetime': event_dt,
                'event_date': event_dt.date(),
                'display_time': rec.get('display_time', event_dt.strftime('%I:%M %p')),
                'event_id': rec.get('id'),
                'status': rec.get('status', ''),
                'is_completed': _is_completed_status(rec.get('status', '')),
                'confirmstatus': rec.get('confirmstatus', '') or 'pending',
                'recurring_event_id': rec.get('recurring_event_id', None),
            }
            events_by_date.setdefault(event_row['event_date'], []).append(event_row)
            if scheduled_member_id_str == current_member_id_str:
                member_events.append(event_row)

        for event_date in events_by_date:
            events_by_date[event_date] = sorted(events_by_date[event_date], key=lambda e: e['event_datetime'])

        member_events = sorted(member_events, key=lambda e: e['event_datetime'])

        return events_by_date, member_events, today_date, local_tz, current_member_id_str

    def get_attendance_panel_data(self, member_id: str, current_datetime: datetime) -> Dict:
        """
        Build data for the attendance confirmation panel: the member's single earliest
        not-yet-completed workout event scheduled for today or tomorrow, their RSVP status
        (read from the calendar event's #confirmstatus tag), and teammates scheduled the same day.
        Reuses the same calendar fetch as get_scheduled_workouts_data (no extra calendar call).
        """
        try:
            events_by_date, member_events, today_date, local_tz, current_member_id_str = self._fetch_team_events(member_id, current_datetime)
            tomorrow_date = today_date + timedelta(days=1)

            candidates = [
                e for e in member_events
                if e['event_date'] in (today_date, tomorrow_date) and not e['is_completed']
            ]
            if not candidates:
                return {'has_event': False}

            attention_event = candidates[0]
            is_today = attention_event['event_date'] == today_date
            day_label = 'today' if is_today else 'tomorrow'

            team_members = [
                {
                    'name': get_member_name_from_member_id(e['member_id']),
                    'time': e['display_time'],
                    'attendance_status': e['confirmstatus'],
                }
                for e in events_by_date.get(attention_event['event_date'], [])
                if e['member_id'] != current_member_id_str
            ]

            data = {
                'has_event': True,
                'event_id': attention_event['event_id'],
                'day_label': day_label,
                'is_today': is_today,
                'scheduled_datetime': attention_event['event_datetime'],
                'display_time': attention_event['display_time'],
                'attendance_status': attention_event['confirmstatus'],
                'team_members': team_members,
                'program_key': None,
                'workout_name': None,
                'workout_key': None,
                'program_workouts': [],
            }

            if is_today:
                current_program = get_members_current_active_program(member_id, current_date_dt=current_datetime)
                if current_program:
                    data['program_key'] = str(current_program.get_composite_key())
                    data['program_workouts'] = get_program_workout_options(current_program)
                    next_workout = get_next_workout_in_program(current_program, member_id)
                    if next_workout:
                        candidate_key = next_workout.get('next_workout_key')
                        if candidate_key:
                            next_workout_definition = self.entity_store.get_item_by_composite_key(candidate_key)
                            if next_workout_definition:
                                data['workout_name'] = next_workout_definition.get('name', 'Selected Workout')
                                data['workout_key'] = str(next_workout_definition.get_composite_key())

            return data
        except Exception as e:
            print(f"Error getting attendance panel data: {e}")
            return {'has_event': False}

    def get_home_page_data(self, member_id: str, current_datetime: datetime = None) -> Dict:
        """
        Get all data needed for the home page sections
        
        Args:
            member_id: The member's ID
            current_datetime: Current date/time (defaults to now)
            
        Returns:
            Dict containing data for all three home page sections
        """
        if current_datetime is None:
            current_datetime = datetime.now(timezone.utc)
            
        return {
            'scheduled_workouts': self.get_scheduled_workouts_data(member_id, current_datetime),
            'completed_workouts': self.get_completed_workouts_data(member_id, current_datetime),
            'analytics': self.get_analytics_data(member_id, current_datetime),
            'member_id': member_id,
            'current_datetime': current_datetime
        }
    
    def get_scheduled_workouts_data(self, member_id: str, current_datetime: datetime) -> Dict:
        """
        Build simplified scheduled-workout dashboard data.

        Presentation model:
        1) Most recent completed workout before today (if any).
        2) All events scheduled for today (completed or not completed).
        3) If none for today, first upcoming event after today.
        """
        try:
            current_program = get_members_current_active_program(member_id, current_date_dt=current_datetime)
            if not current_program:
                return {
                    'workouts_on_calendar': [],
                    'has_active_program': False,
                    'program_name': None,
                    'program_key': None,
                    'previous_completed': None,
                    'todays_events': [],
                    'next_upcoming_after_today': None,
                    'show_next_upcoming': False,
                    'has_today_events': False,
                    'has_any_scheduled': False
                }

            events_by_date, member_events, today_date, local_tz, current_member_id_str = self._fetch_team_events(member_id, current_datetime)

            next_workout_name = 'Selected Workout'
            next_workout_key = None
            next_workout_definition = None
            next_workout = get_next_workout_in_program(current_program, member_id)
            if next_workout:
                candidate_key = next_workout.get('next_workout_key')
                if candidate_key:
                    next_workout_definition = self.entity_store.get_item_by_composite_key(candidate_key)
                    if next_workout_definition:
                        next_workout_name = next_workout_definition.get('name', 'Selected Workout')
                        next_workout_key = str(next_workout_definition.get_composite_key())

            def _coerce_local_datetime(value):
                if not value:
                    return None
                try:
                    dt_value = datetime.fromisoformat(value) if isinstance(value, str) else value
                except (TypeError, ValueError):
                    return None
                if dt_value.tzinfo is None:
                    return local_tz.localize(dt_value)
                return dt_value.astimezone(local_tz)

            # Pull member instances once, then enrich only the small subset needed for dashboard text.
            completed_instances = [
                i for i in self.entity_store.list_items(MemberWorkoutInstanceEntity({'member_id': member_id}))
                if i.get('finished_ts')
            ]
            completed_instances = sorted(completed_instances, key=lambda x: x.get('finished_ts', ''), reverse=True)

            today_completed_event_count = len([
                e for e in member_events
                if e['event_date'] == today_date and e['is_completed']
            ])

            completed_by_date = {today_date: []}
            previous_completed_detail = None
            workout_def_cache = {}

            for instance in completed_instances:
                completed_dt = _coerce_local_datetime(instance.get('finished_ts'))
                if not completed_dt:
                    continue

                include_for_today = (
                    completed_dt.date() == today_date
                    and len(completed_by_date[today_date]) < today_completed_event_count
                )
                include_for_previous = completed_dt.date() < today_date and previous_completed_detail is None

                if not include_for_today and not include_for_previous:
                    if previous_completed_detail is not None and len(completed_by_date[today_date]) >= today_completed_event_count:
                        break
                    continue

                workout_name = instance.get('name', 'Completed Workout')
                workout_key = None
                workout_def_id = instance.get('member_workout_def_id')
                if workout_def_id:
                    if workout_def_id not in workout_def_cache:
                        workout_def_cache[workout_def_id] = self.entity_store.get_item(MemberWorkoutDefinitionEntity({'id': workout_def_id}))
                    workout_def = workout_def_cache.get(workout_def_id)
                    if workout_def:
                        workout_name = workout_def.get('name', workout_name)
                        workout_key = str(workout_def.get_composite_key())

                detail = {
                    'completed_datetime': completed_dt,
                    'workout_name': workout_name,
                    'workout_key': workout_key,
                }

                if include_for_today:
                    completed_by_date[today_date].append(detail)
                if include_for_previous and previous_completed_detail is None:
                    previous_completed_detail = detail

            def _team_members_for_event(event_row: Dict) -> List[Dict]:
                others = [
                    e for e in events_by_date.get(event_row['event_date'], [])
                    if e['member_id'] != current_member_id_str
                ]
                return [
                    {
                        'name': get_member_name_from_member_id(e['member_id']),
                        'time': e['display_time'],
                    }
                    for e in others
                ]

            previous_completed = None
            if previous_completed_detail:
                previous_completed = {
                    'scheduled_datetime': previous_completed_detail['completed_datetime'],
                    'event_id': None,
                    'workout_name': previous_completed_detail.get('workout_name', 'Completed Workout'),
                    'workout_key': previous_completed_detail.get('workout_key'),
                }

            todays_events = []
            today_member_events = [e for e in member_events if e['event_date'] == today_date]
            today_completed_details = sorted(list(completed_by_date.get(today_date, [])), key=lambda c: c['completed_datetime'])
            for event_row in today_member_events:
                completed_detail = None
                if event_row['is_completed'] and today_completed_details:
                    completed_detail = today_completed_details.pop(0)

                todays_events.append({
                    'event_id': event_row['event_id'],
                    'scheduled_datetime': event_row['event_datetime'],
                    'display_time': event_row['display_time'],
                    'status': 'completed' if event_row['is_completed'] else 'upcoming',
                    'is_completed': event_row['is_completed'],
                    'can_start': not event_row['is_completed'],
                    'team_members': _team_members_for_event(event_row),
                    'workout_name': completed_detail.get('workout_name') if completed_detail else next_workout_name,
                    'workout_key': completed_detail.get('workout_key') if completed_detail else next_workout_key,
                    'selected_workout_key': next_workout_key,
                })

            future_events = [
                e for e in member_events
                if e['event_date'] > today_date and not e['is_completed']
            ]
            next_upcoming_after_today = None
            if future_events:
                first_upcoming = future_events[0]
                next_upcoming_after_today = {
                    'event_id': first_upcoming['event_id'],
                    'scheduled_datetime': first_upcoming['event_datetime'],
                    'display_time': first_upcoming['display_time'],
                    'team_members': _team_members_for_event(first_upcoming),
                    'workout_name': next_workout_name,
                    'workout_key': next_workout_key,
                }

            all_todays_events_completed = bool(todays_events) and all(e.get('is_completed') for e in todays_events)
            show_next_upcoming = bool(next_upcoming_after_today) and (not todays_events or all_todays_events_completed)

            legacy_list = todays_events if todays_events else ([next_upcoming_after_today] if next_upcoming_after_today else [])

            return {
                'workouts_on_calendar': legacy_list,
                'has_active_program': True,
                'program_name': current_program.get('name', 'Current Program'),
                'program_key': str(current_program.get_composite_key()),
                'previous_completed': previous_completed,
                'todays_events': todays_events,
                'next_upcoming_after_today': next_upcoming_after_today,
                'show_next_upcoming': show_next_upcoming,
                'has_today_events': len(todays_events) > 0,
                'has_any_scheduled': bool(previous_completed or todays_events or next_upcoming_after_today),
            }
            
        except Exception as e:
            print(f"Error getting scheduled workouts data: {e}")
            return {
                'workouts_on_calendar': [],
                'has_active_program': False,
                'program_name': None,
                'program_key': None,
                'previous_completed': None,
                'todays_events': [],
                'next_upcoming_after_today': None,
                'show_next_upcoming': False,
                'has_today_events': False,
                'has_any_scheduled': False,
            }
    
    def get_completed_workouts_data(self, member_id: str, current_datetime: datetime) -> Dict:
        """
        Get recent completed workouts
        
        Returns data structure:
        {
            'workouts': [
                {
                    'workout_name': str,
                    'workout_instance': dict,
                    'completed_datetime': datetime,
                    'workout_instance_key': str
                }
            ],
            'total_count': int
        }
        """
        try:
            # Query completed workout instances for this member
            # Filter by completion status and sort by date descending
            filter_criteria = {
                'member_id': member_id,
                'status': 'completed'
            }
            
            completed_instances = self.entity_store.list_items(MemberWorkoutInstanceEntity({"member_id": member_id}))
            completed_instances = sorted(completed_instances, key=lambda x: x.get('finished_ts', ''), reverse=True)
            max_completed_to_show = 15
            completed_workouts = []
            for instance in completed_instances:
                if len(completed_workouts) >= max_completed_to_show:
                    break
                # Get workout definition name
                workout_def_id = instance.get('member_workout_def_id')
                workout_def = self.entity_store.get_item(MemberWorkoutDefinitionEntity({'id': workout_def_id}))
                if not workout_def:
                    continue
                workout_name = workout_def.get('name', 'Unnamed Workout')
                if instance.get('finished_ts', None):
                    end_time = datetime.fromisoformat(instance['finished_ts'])
                else:
                    continue

                completed_workouts.append({
                    'workout_name': workout_name,
                    'workout_instance': instance,
                    'completed_datetime': end_time,
                    'workout_instance_key': instance.get_composite_key()
                })
            
            return {
                'workouts': completed_workouts,
                'total_count': len(completed_workouts)
            }
            
        except Exception as e:
            print(f"Error getting completed workouts data: {e}")
            return {
                'workouts': [],
                'total_count': 0
            }
    
    def get_analytics_data(self, member_id: str, current_datetime: datetime) -> Dict:
        """
        Get analytics data for reports
        
        Returns data structure:
        {
            'weekly_summary': {
                'workouts_this_week': int,
                'total_duration_minutes': int,
                'avg_duration_minutes': float,
                'most_common_workout': str,
                'completion_rate': float
            },
            'available_reports': [
                {'name': str, 'description': str, 'type': str}
            ]
        }
        """
        try:
            # Calculate start of current week (Monday)
            days_since_monday = current_datetime.weekday()
            week_start = current_datetime - timedelta(days=days_since_monday)
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = week_start.replace(tzinfo=pytz.timezone('US/Eastern'))
            # Get completed workouts for this week
            filter_criteria = {
                'member_id': member_id,
                'status': 'completed'
            }
            
            workout_instances = list(self.entity_store.list_items(MemberWorkoutInstanceEntity({"member_id": member_id})))
            all_completed = [c for c in workout_instances if c.get('finished_ts', None)]
            all_completed = sorted(all_completed, key=lambda x: x.get('finished_ts', ''), reverse=True)
            
            # Filter to this week only
            this_week_workouts = []
            for workout in all_completed:
                end_time = workout.get('finished_ts')
                if end_time:
                    end_dt = datetime.fromisoformat(end_time) if isinstance(end_time, str) else end_time
                    end_dt = end_dt.replace(tzinfo=pytz.timezone('US/Eastern'))
                    if end_dt >= week_start:
                        this_week_workouts.append(workout)
            
            # Calculate weekly summary
            weekly_summary = self._calculate_weekly_summary(this_week_workouts)
            
            # Define available reports
            available_reports = [
                {
                    'name': 'Weekly Summary',
                    'description': 'Overview of this week\'s workout activity',
                    'type': 'summary'
                },
                {
                    'name': 'Progress Trends',
                    'description': 'Charts showing workout progress over time',
                    'type': 'chart'
                },
                {
                    'name': 'Exercise Performance',
                    'description': 'Detailed analysis of individual exercise performance',
                    'type': 'detailed'
                }
            ]
            
            return {
                'weekly_summary': weekly_summary,
                'available_reports': available_reports
            }
            
        except Exception as e:
            print(f"Error getting analytics data: {e}")
            return {
                'weekly_summary': {
                    'workouts_this_week': 0,
                    'total_duration_minutes': 0,
                    'avg_duration_minutes': 0.0,
                    'most_common_workout': 'None',
                    'completion_rate': 0.0
                },
                'available_reports': []
            }
    
    def _can_start_workout(self, workout_datetime: datetime, current_datetime: datetime) -> bool:
        """Check if workout can be started (within 6 hours or same day)"""
        if current_datetime.tzinfo is None:
            current_datetime = current_datetime.replace(tzinfo=timezone.utc)
        if workout_datetime.tzinfo is not None:
            current_datetime = current_datetime.astimezone(workout_datetime.tzinfo)

        time_diff = (workout_datetime - current_datetime).total_seconds()
        same_day = workout_datetime.date() == current_datetime.date()
        
        # Can start if within 6 hours before or anytime on same day
        return time_diff <= 6 * 3600 and (time_diff > -24 * 3600 or same_day)
    
    def _get_workout_status(self, workout_datetime: datetime, current_datetime: datetime) -> str:
        """Determine workout status: upcoming, available, or missed"""
        if current_datetime.tzinfo is None:
            current_datetime = current_datetime.replace(tzinfo=timezone.utc)
        if workout_datetime.tzinfo is not None:
            current_datetime = current_datetime.astimezone(workout_datetime.tzinfo)

        time_diff = (workout_datetime - current_datetime).total_seconds()
        same_day = workout_datetime.date() == current_datetime.date()

        # Same-day workouts are treated as upcoming for dashboard display.
        if same_day:
            return 'upcoming'

        # Upcoming if it's still in the future and outside the immediate start window.
        if time_diff > 6 * 3600:
            return 'upcoming'

        # Available for a short window around scheduled time (6 hours before/after).
        if -6 * 3600 <= time_diff <= 6 * 3600:
            return 'available'

        # Otherwise it is in the past and outside the start window.
        return 'missed'
    
    def _get_team_members_for_time_slot(self, member_id: str, workout_datetime: datetime) -> List[Dict]:
        """
        Get team members scheduled around the same time
        This is a placeholder - assumes backend API exists
        """
        # TODO: Implement actual API call to get team members
        # For now, return mock data
        return [
            {'name': 'John Smith', 'id': 'member_123'},
            {'name': 'Sarah Johnson', 'id': 'member_456'}
        ]

    def _limit_scheduled_workouts_display(self, workouts: List[Dict], current_datetime: datetime) -> List[Dict]:
        """
        Limit scheduled workouts shown on home dashboard.

        Rules:
        1) Always include the next upcoming workout.
        2) Include the immediately prior workout only if it was missed.
        3) After the next upcoming workout, include only the next two scheduled workouts.
        4) Return at most five workouts.
        """
        if not workouts:
            return []

        sorted_workouts = sorted(workouts, key=lambda w: w.get('scheduled_datetime', datetime.min.replace(tzinfo=timezone.utc)))

        next_upcoming_idx = None
        current_date = current_datetime.date()

        # Anchor display on first workout scheduled for today or later.
        for idx, workout in enumerate(sorted_workouts):
            scheduled_datetime = workout.get('scheduled_datetime')
            if not scheduled_datetime:
                continue
            if scheduled_datetime.tzinfo is not None and current_datetime.tzinfo is not None:
                current_date = current_datetime.astimezone(scheduled_datetime.tzinfo).date()
            if scheduled_datetime.date() >= current_date:
                next_upcoming_idx = idx
                break

        if next_upcoming_idx is None:
            return []

        selected_indices = set()
        selected_indices.add(next_upcoming_idx)

        prior_idx = next_upcoming_idx - 1
        if prior_idx >= 0 and sorted_workouts[prior_idx].get('status') == 'missed':
            selected_indices.add(prior_idx)

        for offset in (1, 2):
            next_idx = next_upcoming_idx + offset
            if next_idx < len(sorted_workouts):
                selected_indices.add(next_idx)

        limited_workouts = [sorted_workouts[i] for i in sorted(selected_indices)]
        return limited_workouts[:4]
    
    def _calculate_weekly_summary(self, workouts: List[Dict]) -> Dict:
        """Calculate weekly summary statistics"""
        if not workouts:
            return {
                'workouts_this_week': 0,
                'total_duration_minutes': 0,
                'avg_duration_minutes': 0.0,
                'most_common_workout': 'None',
                'completion_rate': 0.0
            }
        
        total_duration = 0
        workout_names = []
        
        for workout in workouts:
            # Calculate duration
            start_time = workout.get('start_datetime')
            end_time = workout.get('end_datetime')
            
            if start_time and end_time:
                start_dt = datetime.fromisoformat(start_time) if isinstance(start_time, str) else start_time
                end_dt = datetime.fromisoformat(end_time) if isinstance(end_time, str) else end_time
                duration = int((end_dt - start_dt).total_seconds() / 60)
                total_duration += duration
            
            # Track workout names
            workout_key = workout.get('workout_definition_key')
            if workout_key:
                workout_def = self.entity_store.get_item_by_composite_key(workout_key)
                if workout_def:
                    workout_names.append(workout_def.get('name', 'Unnamed'))
        
        # Find most common workout
        most_common = 'None'
        if workout_names:
            from collections import Counter
            counter = Counter(workout_names)
            most_common = counter.most_common(1)[0][0]
        
        # Calculate averages
        avg_duration = total_duration / len(workouts) if workouts else 0
        
        # TODO: Calculate actual completion rate based on scheduled vs completed
        completion_rate = 85.0  # Placeholder
        
        return {
            'workouts_this_week': len(workouts),
            'total_duration_minutes': total_duration,
            'avg_duration_minutes': round(avg_duration, 1),
            'most_common_workout': most_common,
            'completion_rate': completion_rate
        }
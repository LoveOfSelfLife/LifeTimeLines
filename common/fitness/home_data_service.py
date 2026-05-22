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


class HomePageDataService:
    """Service for aggregating all home page data"""
    
    def __init__(self):
        self.entity_store = EntityStore()
        
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
        Get scheduled workouts for the next week
        
        Returns data structure:
        {
            'workouts': [
                {
                    'workout_name': str,
                    'workout_definition': dict,
                    'scheduled_datetime': datetime,
                    'can_start': bool,
                    'time_until_workout': int (seconds),
                    'team_members': [{'name': str, 'id': str}],
                    'event_id': str,
                    'status': 'upcoming|available|missed|completed'
                }
            ],
            'has_active_program': bool,
            'program_name': str
        }
        """
        try:
            # Get member's current program
            current_program = get_members_current_active_program(member_id, current_date_dt=current_datetime)
            if not current_program:
                return {
                    'workouts': [],
                    'has_active_program': False,
                    'program_name': None
                }
            # get the member's team members.  We will use this to only find workouts that are scheduled for the member and the member's team members.
            current_team = get_current_team_context(member_id)        
            team_members = get_team_members(current_team['id'])
            team_coaches = get_team_coaches(current_team['id'])
            all_members_of_team = [tm.get('member_id') for tm in team_members] + [tc.get('coach_id') for tc in team_coaches]         
            team_member_filter_func = lambda m_id: any(tm_id == m_id for tm_id in all_members_of_team)
            # Get scheduled events from calendar for next 7 days
            cal = get_calendar_service()
            start_date = current_datetime.strftime("%Y-%m-%d")
            end_date = (current_datetime + timedelta(days=7)).strftime("%Y-%m-%d")
            scheduled_calendar_events, sorted_events = cal.get_dates_and_events_stream(date_min=start_date, date_max=end_date, filter_by_member_id_func=team_member_filter_func)
            
            scheduled_workouts_by_date_list = []

            scheduled_workouts_by_date = {
                'members_scheduled' : []
            }
            for rec in scheduled_calendar_events:
                if rec.get('type') == 'date':
                    # if this date has no members, then reuse it
                    if len(scheduled_workouts_by_date.get('members_scheduled')) == 0:
                        scheduled_workouts_by_date['date'] = rec.get('display_date')
                    else:
                        # otherwise, we need to start a new scheduled workout
                        scheduled_workouts_by_date_list.append(scheduled_workouts_by_date)
                        scheduled_workouts_by_date = {
                            'date': rec.get('display_date'),
                            'members_scheduled' : []
                        }
                elif rec.get('type') == 'event':
                    # this is an event on the calendar that indicates a member is scheduled for a workout on this date, 
                    # we will add the member to the current scheduled workout's members_scheduled list
                    scheduled_member_id = rec.get('member_id')
                    scheduled_display_time = rec.get('display_time')
                    scheduled_time = rec.get('time')
                    scheduled_date = rec.get('date')
                    scheduled_event_id = rec.get('id')
                    scheduled_event_status = rec.get('status')
                    if scheduled_event_status == 'done':
                        continue
                    scheduled_member = { 'member_id': scheduled_member_id, 
                                        'scheduled_display_time': scheduled_display_time, 
                                        'scheduled_time': scheduled_time, 
                                        'scheduled_date': scheduled_date, 
                                        'event_id': scheduled_event_id, 
                                        'status': scheduled_event_status }
                    scheduled_workouts_by_date['members_scheduled'] = scheduled_workouts_by_date['members_scheduled'] + [scheduled_member]
            
            # this is for the last scheduled workout that we were building in the loop, we need to add it to the list if it has any members scheduled for it
            if len(scheduled_workouts_by_date.get('members_scheduled')) > 0:
                scheduled_workouts_by_date_list.append(scheduled_workouts_by_date)

            final_scheduled_workout_by_date = []
            is_my_first_incomplete_workout_event = True

            for workouts_on_date in scheduled_workouts_by_date_list:
                # if the current member is scheduled to workout on this date, then we will include it in the output stream
                if member_id in [m['member_id'] for m in workouts_on_date.get('members_scheduled', [])]:
                    # this event is for the current member
                    member_workouts_scheduled_for_date = workouts_on_date.get('members_scheduled', [])

                    if is_my_first_incomplete_workout_event:
                        next_workout = get_next_workout_in_program(current_program, member_id)
                        workout_key = next_workout.get('next_workout_key')
                        workout_definition = self.entity_store.get_item_by_composite_key(workout_key)
                        is_my_first_incomplete_workout_event = False
                    else:
                        workout_definition = None
                    my_event = list(filter(lambda m: m['member_id'] == member_id, member_workouts_scheduled_for_date))
                    if not my_event:
                        continue
                    my_event = my_event[0]
                    
                    # Parse event datetime
                    # my_event['scheduled_date'] is a datetime.date object, and my_event['scheduled_time'] is a string in the format "HH:MM"
                    # need to combine these into a single datetime object for the event
                    # also need to make sure to set the timezone for the event datetime to be the set to the local timezone (e.g. US/Eastern) so that the time until workout calculation is correct
                    event_datetime = datetime.combine(my_event['scheduled_date'], datetime.strptime(my_event['scheduled_time'], "%H:%M").time())
                    event_datetime = event_datetime.replace(tzinfo=pytz.timezone('US/Eastern'))

                    time_until_workout = int((event_datetime - current_datetime).total_seconds())
                    
                    # Determine if workout can be started (within 6 hours or same day)
                    can_start = self._can_start_workout(event_datetime, current_datetime)
                    
                    # Determine workout status
                    status = self._get_workout_status(event_datetime, current_datetime)
                    
                    # # Get team members scheduled around same time (placeholder for API call)
                    team_members = [m for m in member_workouts_scheduled_for_date if m['member_id'] != member_id]
                    # we want to display the member's name and the time they are scheduled for in the team members list, so we will create a new list of strings that combines the member's name and the time they are scheduled for
                    team_members2 = [ { 'name': get_member_name_from_member_id(m['member_id']), 'time':f"{m['scheduled_display_time']}" } for m in team_members ]

                    final_scheduled_workout_by_date.append({
                        'workout_name': workout_definition.get('name', 'Unnamed Workout') if workout_definition else None,
                        'workout_definition': workout_definition,
                        'scheduled_datetime': event_datetime,
                        'can_start': can_start,
                        'time_until_workout': time_until_workout,
                        'team_members': team_members2,
                        'event_id': my_event.get('event_id'),
                        'status': status
                    })
            
            return {
                'workouts': final_scheduled_workout_by_date,
                'has_active_program': True,
                'program_name': current_program.get('name', 'Current Program'),
                'program_key': str(current_program.get_composite_key())
            }
            
        except Exception as e:
            print(f"Error getting scheduled workouts data: {e}")
            return {
                'workouts': [],
                'has_active_program': False,
                'program_name': None
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
                workout_def = self.entity_store.get_item(MemberWorkoutDefinitionEntity({'id': workout_def_id, 'member_id': member_id}))
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
        time_diff = (workout_datetime - current_datetime).total_seconds()
        same_day = workout_datetime.date() == current_datetime.date()
        
        # Can start if within 6 hours before or anytime on same day
        return time_diff <= 6 * 3600 and (time_diff > -24 * 3600 or same_day)
    
    def _get_workout_status(self, workout_datetime: datetime, current_datetime: datetime) -> str:
        """Determine workout status: upcoming, available, or missed"""
        time_diff = (workout_datetime - current_datetime).total_seconds()
        same_day = workout_datetime.date() == current_datetime.date()
        
        if same_day or time_diff <= 6 * 3600:
            return 'available'
        elif workout_datetime.date() < current_datetime.date():
            return 'missed'
        else:
            return 'upcoming'
    
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
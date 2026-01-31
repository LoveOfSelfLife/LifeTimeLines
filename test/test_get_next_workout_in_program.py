import unittest
import sys
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add the common directory to the path so we can import the module under test
sys.path.insert(0, 'd:\\GitHub\\DickKemp\\LifeTimeLines')

from common.fitness.programs import get_next_workout_in_program


class TestGetNextWorkoutInProgram(unittest.TestCase):
    """
    Test the get_next_workout_in_program method with various scenarios.
    
    The method should return the workout that was least recently done,
    with workouts that have never been done taking priority.
    """
    
    def setUp(self):
        """Set up test data"""
        # Mock program data
        self.program = {
            'id': 'program-123',
            'name': 'Test Program',
            'start_date': '2026-01-01T00:00:00',
            'end_date': '2026-12-31T23:59:59'
        }
        
        # Mock workouts in program
        self.workouts_in_program = [
            {'id': 'workout-1', 'name': 'Push Day'},
            {'id': 'workout-2', 'name': 'Pull Day'},
            {'id': 'workout-3', 'name': 'Leg Day'}
        ]
        
        # Mock workout instances (completed workouts)
        self.workout_instances = [
            {
                'id': 'instance-1',
                'member_workout_def_id': 'workout-1',
                'finished_ts': '2026-01-20T10:00:00'
            },
            {
                'id': 'instance-2', 
                'member_workout_def_id': 'workout-2',
                'finished_ts': '2026-01-22T10:00:00'
            },
            {
                'id': 'instance-3',
                'member_workout_def_id': 'workout-1',
                'finished_ts': '2026-01-25T10:00:00'
            }
        ]
        
        self.member_id = 'member-456'

    @patch('common.fitness.programs.DATAMODEL_VERSION', 2)
    @patch('common.fitness.programs.get_workouts_in_program')
    @patch('common.fitness.programs.get_list_of_entities')
    def test_program_has_no_workouts(self, mock_get_list_of_entities, mock_get_workouts_in_program):
        """Test when a program has no workouts - should return None"""
        # Setup mocks
        mock_get_workouts_in_program.return_value = []  # No workouts
        mock_get_list_of_entities.return_value = []
        
        # Execute
        result = get_next_workout_in_program(self.program, self.member_id)
        
        # Assert
        self.assertIsNone(result)
        mock_get_workouts_in_program.assert_called_once_with(self.program, self.member_id)

    @patch('common.fitness.programs.DATAMODEL_VERSION', 2)
    @patch('common.fitness.programs.get_workouts_in_program')
    @patch('common.fitness.programs.get_list_of_entities')
    def test_program_has_workouts_no_instances(self, mock_get_list_of_entities, mock_get_workouts_in_program):
        """Test when program has workouts but member has never done any - should return first workout"""
        # Setup mocks
        mock_get_workouts_in_program.return_value = self.workouts_in_program
        mock_get_list_of_entities.return_value = []  # No completed instances
        
        # Execute
        result = get_next_workout_in_program(self.program, self.member_id)
        
        # Assert
        self.assertEqual(result, self.workouts_in_program[0])  # Should return first workout
        mock_get_workouts_in_program.assert_called_once_with(self.program, self.member_id)
        mock_get_list_of_entities.assert_called_once_with("MemberWorkoutInstanceTable", partition_key=self.member_id)

    @patch('common.fitness.programs.DATAMODEL_VERSION', 2)
    @patch('common.fitness.programs.get_workouts_in_program')
    @patch('common.fitness.programs.get_list_of_entities')
    def test_program_with_multiple_completed_workouts(self, mock_get_list_of_entities, mock_get_workouts_in_program):
        """Test when member has done multiple workouts - should return least recently done workout"""
        # Setup mocks
        mock_get_workouts_in_program.return_value = self.workouts_in_program
        mock_get_list_of_entities.return_value = self.workout_instances
        
        # Execute
        result = get_next_workout_in_program(self.program, self.member_id)
        
        # Assert
        # Based on workout_instances:
        # - workout-1 was done on 2026-01-20 and 2026-01-25 (most recent: 2026-01-25)
        # - workout-2 was done on 2026-01-22 (most recent: 2026-01-22) 
        # - workout-3 was never done (most recent: empty string)
        # workout-3 should be returned as it was never done (empty string sorts first)
        expected_workout = self.workouts_in_program[2]  # workout-3 (Leg Day)
        self.assertEqual(result, expected_workout)
        
        mock_get_workouts_in_program.assert_called_once_with(self.program, self.member_id)
        mock_get_list_of_entities.assert_called_once_with("MemberWorkoutInstanceTable", partition_key=self.member_id)

    @patch('common.fitness.programs.DATAMODEL_VERSION', 2)
    @patch('common.fitness.programs.get_workouts_in_program')
    @patch('common.fitness.programs.get_list_of_entities')
    def test_all_workouts_done_returns_least_recent(self, mock_get_list_of_entities, mock_get_workouts_in_program):
        """Test when all workouts have been done - should return the least recently done"""
        # Setup mocks - all workouts have been completed
        mock_get_workouts_in_program.return_value = self.workouts_in_program
        
        # Add instances for all workouts
        all_workout_instances = self.workout_instances + [
            {
                'id': 'instance-4',
                'member_workout_def_id': 'workout-3',
                'finished_ts': '2026-01-21T10:00:00'  # Done between workout-1 and workout-2
            }
        ]
        mock_get_list_of_entities.return_value = all_workout_instances
        
        # Execute
        result = get_next_workout_in_program(self.program, self.member_id)
        
        # Assert
        # Order of most recent completion:
        # - workout-1: most recent = 2026-01-25 (latest)
        # - workout-2: most recent = 2026-01-22 (middle)
        # - workout-3: most recent = 2026-01-21 (oldest)
        # 
        # workout-3 should be returned as it was least recently done
        expected_workout = self.workouts_in_program[2]  # workout-3 (Leg Day)
        self.assertEqual(result, expected_workout)
        self.assertEqual(result, expected_workout)

    @patch('common.fitness.programs.DATAMODEL_VERSION', 2)
    @patch('common.fitness.programs.get_workouts_in_program')
    @patch('common.fitness.programs.get_list_of_entities')
    def test_instances_not_in_program_filtered_out(self, mock_get_list_of_entities, mock_get_workouts_in_program):
        """Test that workout instances not in the current program are filtered out"""
        # Setup mocks
        mock_get_workouts_in_program.return_value = self.workouts_in_program
        
        # Add instances from other programs that should be filtered out
        instances_with_other_programs = self.workout_instances + [
            {
                'id': 'instance-other',
                'member_workout_def_id': 'workout-other-program',
                'finished_ts': '2026-01-28T10:00:00'
            }
        ]
        mock_get_list_of_entities.return_value = instances_with_other_programs
        
        # Execute
        result = get_next_workout_in_program(self.program, self.member_id)
        
        # Assert
        # Should still return workout-3 as it's never been done (ignoring the other program instance)
        expected_workout = self.workouts_in_program[2]  # workout-3 (Leg Day)
        self.assertEqual(result, expected_workout)


if __name__ == '__main__':
    unittest.main()
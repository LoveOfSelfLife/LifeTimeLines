
from common.entity_store import EntityObject
from common.fitness.entities_getter import get_entity

class WorkoutEntity (EntityObject):
    table_name="WorkoutTable"
    fields=["id", "name", "sections", "created_ts", "created_by"]
    key_field="id"
    partition_value="workout"

    def __init__(self, d={}):
        super().__init__(d)

class ProgramWorkoutEntity (EntityObject):
    table_name="ProgramWorkoutTable"
    fields=["id", "name", "sections", "created_ts", "created_by", "program_id", "parent_workout_id"]
    key_field="id"
    partition_field="program_id"

    def __init__(self, d={}):
        super().__init__(d)

class ProgramWorkoutInstanceEntity (EntityObject):
    table_name="ProgramWorkoutInstanceTable"
    fields=["id", "program_workout_id", "name", "sections"]
    key_field="id"
    partition_field="program_workout_id"

    def __init__(self, d={}):
        super().__init__(d)


def get_exercises_from_workout(workout):
    exercises = []
    for s in workout['sections']:
        for it in s['exercises']:
            ex = get_entity("ExerciseTable", it['id'])
            if ex:
                ex['parameters'] = it['parameters']
                exercises.append(ex)
    return exercises


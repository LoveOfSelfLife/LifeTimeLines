from datetime import datetime
import os
from dotenv import load_dotenv
import json
from common.entity_store import EntityStore
from common.fitness.exercise_entity import ExerciseEntity
from common.fitness.member_entity import MemberEntity
from common.fitness.member_exercise_history import MemberExerciseEventHistoryEntity, MemberPerformsExerciseEntity, extract_and_load_exercise_events_from_workout_instance
from common.fitness.member_workout_entity import MemberWorkoutInstanceEntity, WorkoutDefinitionEntity
from common.table_store import TableStore
from common.blob_store import BlobStore
from services.fitnessclub.views import exercises


def init():
    load_dotenv('../.env')
    print(f"Current working directory: {os.getcwd()}")
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
    BlobStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

def list_alf_exercises():
    
    es = EntityStore()
    exercises = list(es.list_items(ExerciseEntity()))
    for exercise in exercises:
        if exercise['origin'] == 'ALF-workout-images':
            print(f"{exercise.get('name', None)}")

def list_alf_programs():
    
    es = EntityStore()
    programs = list(es.list_items(WorkoutDefinitionEntity()))
    for program in programs:
        # if name begins with "ALF" then print it out
        if program['name'].startswith('ALF'):
            print(f"{program.get('name', None)}")

def modify_alf_program_names():
    
    es = EntityStore()
    programs = list(es.list_items(WorkoutDefinitionEntity()))
    renamed_programs = []
    for program in programs:
        # if name begins with "ALF" then print it out
        if program['name'].startswith('ALF'):
            program['name'] = program['name'].replace('ALF', 'RICH')
            # print(f"{program.get('name', None)}")
            renamed_programs.append(program)
    if renamed_programs:
        es.upsert_items(renamed_programs)
        print(f"Renamed {len(renamed_programs)} programs.")
    else:
        print("No programs to rename.")

def export_exercises_to_csv():
    # export all exercises to a CSV file using pipe '|' delimeter, with columns: id, name, description, category, force type, physical fitness component, primary muscles, origin

    es = EntityStore()
    exercises = list(es.list_items(ExerciseEntity()))
    with open('exercises_export.csv', 'w') as f:
        f.write('id|name|description|category|force_type|physical_fitness_component|primary_muscles|equipment|set_completion_measure|origin\n')
        for exercise in exercises:
            id = exercise.get('id', '')
            name = exercise.get('name', '').replace('|', ' ')
            # only keep the first 200 characters of the description to avoid excessively long entries in the CSV
            # also remove any newlines or carriage returns or pipe characters from the description to avoid breaking the CSV format
            description = exercise.get('instructions', '').replace('|', ' ').replace('\n', ' ').replace('\r', ' ')[:200]
            category = exercise.get('category', '').replace('|', ' ')
            force = exercise.get('force', '').replace('|', ' ') if exercise.get('force', '') else ''
            physical_fitness_components = exercise.get('physical_fitness_components', [])
            physical_fitness_components = ','.join(physical_fitness_components).replace('|', ' ') if physical_fitness_components else ''
            primaryMuscles = exercise.get('primaryMuscles', [])
            primaryMuscles = ','.join(primaryMuscles).replace('|', ' ') if primaryMuscles else ''
            equipment = exercise.get('equipment', '')
            setCompletionMeasure = exercise.get('setCompletionMeasure', '').replace('|', ' ')
            origin = exercise.get('origin', '')
            s = f"{id}|{name}|{description}|{category}|{force}|{physical_fitness_components}|{primaryMuscles}|{equipment}|{setCompletionMeasure}|{origin}\n"
            f.write(s)
    print(f"Exported {len(exercises)} exercises to exercises_export.csv")

if __name__ == '__main__':
    # Initialize the environment and r
    init()
    # list_alf_exercises()
    # list_alf_programs()
    # modify_alf_program_names()
    export_exercises_to_csv()

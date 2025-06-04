
import os
from dotenv import load_dotenv
import json
from common.entity_store import EntityStore
# from common.fitness.exercise_entity import ExerciseEntity, ExerciseEntityBackup, ExerciseReviewEntity
from common.fitness.workout_entity import WorkoutEntity, WorkoutInstanceEntity
from common.table_store import TableStore
from common.blob_store import BlobStore
from common.fitness.exercises_loader import load_exercise_into_index_table, exercise_generator, load_exercises
from common.fitness.exercise_entity import ExerciseIndexEntity


def init():
    load_dotenv('../.env')
    TableStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))
    BlobStore.initialize(os.getenv('AZURE_STORAGETABLE_CONNECTIONSTRING', None))

    
        
def workouts1():
    es = EntityStore()
    workout_entity = WorkoutEntity()
    
    workouts = list(es.list_items2(workout_entity))
    print(f"number of workouts: {len(workouts)}")
    # for workout in workouts:
    #     print(workout)

def workouts2():
    es = EntityStore()
    workout_entity = WorkoutInstanceEntity()
    
    workouts = list(es.list_items2(workout_entity, dfilter=[]))
    print(f"number of workouts: {len(workouts)}")
    # for workout in workouts:
    #     print(workout)

    # "id", "member_id", "name", "sections", "created_ts", "created_by"
    w = { "id": "workout123",
      "member_id": "70a14cf9-834d-4a9b-a266-95f1c1a772e6",
      "name": "Morning Workout",
      "sections": [],
      "created_ts": "2025-06-02T12:00:00Z",
      "created_by": "70a14cf9-834d-4a9b-a266-95f1c1a772e6"
      }
    
    es.upsert_item(WorkoutInstanceEntity(WorkoutInstanceEntity(w)))

def workouts3():
    es = EntityStore()
    
    # "id", "member_id", "name", "sections", "created_ts", "created_by"
    w = { "id": "workout123",
      "member_id": "70a14cf9-834d-4a9b-a266-95f1c1a772e6",
      "name": "Morning Workout",
      "sections": [],
      "created_ts": "2025-06-02T12:00:00Z",
      "created_by": "70a14cf9-834d-4a9b-a266-95f1c1a772e6"
      }
    
    es.upsert_item(WorkoutInstanceEntity(w))

def workouts4():
    es = EntityStore()

    # "id", "member_id", "name", "sections", "created_ts", "created_by"
    w = { "id": "workout1234",
      "member_id": "43f641cc-9aea-410a-86a2-0a9256ce9188",
      "name": "afternoon Workout",
      "sections": [],
      "created_ts": "2025-06-02T12:10:00Z",
      "created_by": "43f641cc-9aea-410a-86a2-0a9256ce9188"
      }
    
    es.upsert_item(WorkoutInstanceEntity(w))

def workouts5():
    es = EntityStore()
    workout_instance_entity = WorkoutInstanceEntity()
    
    workouts = list(es.list_items2(workout_instance_entity, dfilter=[]))
    print(f"number of workouts: {len(workouts)}")
    # for workout in workouts:
    #     print(workout)

    workout_instance_entity2 = WorkoutInstanceEntity({"member_id": "43f641cc-9aea-410a-86a2-0a9256ce9188",})
    workouts = list(es.list_items2(workout_instance_entity2, dfilter=[]))
    print(f"number of workouts: {len(workouts)}")
    # for workout in workouts:
    #     print(workout)

    workout_instance_entity3 = WorkoutInstanceEntity({"member_id": "workout",})
    workouts = list(es.list_items2(workout_instance_entity3, dfilter=[]))
    print(f"number of workouts: {len(workouts)}")
    # for workout in workouts:
    #     print(workout)

# def apply_exercise_review_findings(exercise_map, exercise_review_map):
#     for exercise in exercise_map.values():
#         print(f"Processing exercise: {exercise['name']}")
#         exercise_review = exercise_review_map.get(exercise['id'], None)
#         if exercise_review:
#             print(f"Found review for exercise: {exercise['name']}")
#             disposition = exercise_review.get('disposition', None)
#             if disposition and 'hide' in disposition:
#                 print(f"Hiding exercise: {exercise['name']}")
#                 exercise['hide'] = True
#             components = exercise_review.get('category', [])
#             if components:
#                 print(f"Setting components for exercise: {exercise['name']}")
#                 exercise['physical_fitness_components'] = components
#             else:
#                 print(f"No components found for exercise: {exercise['name']}")
#                 exercise['physical_fitness_components'] = []
#             comments  = exercise_review.get('comments', None)
#             if comments:
#                 if 'foam' in comments:
#                     print(f"Setting equipment detail for exercise: {exercise['name']}")
#                     components = exercise['physical_fitness_components']
#                     if 'myofascia' not in components:
#                         components.append('myofascia')
#                         exercise['physical_fitness_components'] = components
#                     exercise['equipment'] = "foam_roll"
#             set_completion_measure = exercise_review.get('setCompletionMeasure', None)
#             if set_completion_measure:
#                 exercise['setCompletionMeasure'] = set_completion_measure

#     return exercise_map

# def transform_exercise_table(f):
#     es = EntityStore()
#     exercises = []
#     for e in es.list_items(ExerciseEntity()):
#         exercises.append(e)
#     print(f"number of exercises: {len(exercises)}")
#     updated_exercises = []
#     for exercise in exercises:
#         # Transform the exercise data as needed
#         transformed_exercise = ExerciseEntity(f(exercise))
#         updated_exercises.append(transformed_exercise)
#     es.upsert_items(updated_exercises)

# def export_exercises(json_file = "exercise_export.json"):
#     es = EntityStore()
#     exercises = []
#     for e in es.list_items(ExerciseEntity()):
#         exercises.append(e)
#     export_exercises2(updated_exercises, json_file)

# def export_exercises2(updated_exercises, json_file):
#     with open(json_file, "w") as f:
#         json.dump(updated_exercises, fp=f, indent=4)

# def transform_instructions(exercise_data):
#     # Transform the exercise instructions from a list of strings into a single string delimited by new lines
#     exercise = exercise_data.copy()
#     if exercise.get("instructions", None) is None:
#         exercise["instructons"] = ""
#     if isinstance(exercise["instructions"], list):
#         exercise["instructions"] = "\n".join(exercise["instructions"])
#     exercise['setCompletionMeasure'] = "reps"
#     return exercise 

# def convert_image_id_to_url(exercise_data):
#     # Transform the exercise instructions from a list of strings into a single string delimited by new lines
#     exercise = exercise_data.copy()
#     base_url = "https://ltltablestorage.blob.core.windows.net/fitness-media"
#     if exercise.get("images", None) is None:
#         exercise["images"] = []
#     else:
#         for img in exercise["images"]:
#             if 'id' not in img:
#                 continue
#             img['url'] = f"{base_url}/{img['id']}"
#             del img['id']  # remove the id field
#     return exercise 

# def transform_exercise(exercise_data):
#     # Transform the exercise data as needed
#     # For example, let's just return the exercise as is for now
#     exercise = exercise_data.copy()
#     if exercise.get("images") is None:
#         exercise["images"] = []
#     for img in exercise["images"]:
#         # replace space with a dash in the image name
#         img['type'] = img['description'].replace(" ", "-").lower()
#         img['description'] = f"{img['description']}"
#     if exercise.get("videos") is None:
#         exercise["videos"] = []
#     exercise['equipment_detail'] = ""
#     exercise['origin'] = "exercises.json"
#     return exercise 


if __name__ == '__main__':
    # Initialize the environment 
    init()
    print("Starting workouts experiment..........................................................................................")
    workouts1()
    print("Starting workouts2 experiment..........................................................................................")
    workouts2()
    print("Starting workouts3 experiment..........................................................................................")
    workouts3()
    print("Starting workouts4 experiment..........................................................................................")
    workouts4()    
    print("Re- Starting workouts2 experiment........................................................................................")
    workouts2()
    print("Re- Starting workouts5 experiment........................................................................................")
    workouts5()
    # backup_exercise_table()
    # exercise_map, exercise_review_map = load_exercises_and_reviews()
    # exercise_map2 = apply_exercise_review_findings(exercise_map, exercise_review_map)
    # exercises = sorted(list(exercise_map2.values()), key=lambda x: x['name'].lower())
    # export_exercises2(exercises, json_file="exercise_export.json")
    # update_exercise_table(exercises)
    
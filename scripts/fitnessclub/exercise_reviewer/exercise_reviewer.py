from flask import Flask, render_template, request, send_from_directory
from pathlib import Path
from common.fitness.exercise_entity import MOVEMENT_CATEGORIES, MUSCLES, PHYSICAL_FITNESS_COMPONENTS, EQUIPMENT
import json
import threading

app = Flask(__name__)

VIDEO_DIR = Path("C:/Users/richk/Downloads/ALF_videos/videos")
INPUT_EXERCISES_FILE = Path("vimeo_exercises.json")
# INPUT_EXERCISES_FILE = Path("tbl_store_exercises.json")
# OUTPUT_EXERCISES_FILE = Path("classified_exercises.json")

# Groups of classification flags, each rendered as its own section in the UI.
# Keys are the JSON field names used to persist each group's selections.
CATEGORIES = {
    "movements": {"label": "Movements", "flags": MOVEMENT_CATEGORIES},
    "muscles": {"label": "Muscles", "flags": MUSCLES},
    "fitness": {"label": "Fitness Components", "flags": PHYSICAL_FITNESS_COMPONENTS},
    "equipment": {"label": "Equipment", "flags": EQUIPMENT},
    "custom": {"label": "Custom Attributes", "flags": ["reps", "time", "distance", "calories", "resistance_doubled", "only_one_set", "combination"]},
}

state_lock = threading.Lock()

def load_exercises():
    # before we start, we want to make a copy of the input exercise file in the same folder
    # but we want to append a timestamp to avoid overwriting existing copies.
    import shutil
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_file = INPUT_EXERCISES_FILE.with_name(f"{INPUT_EXERCISES_FILE.stem}_{timestamp}{INPUT_EXERCISES_FILE.suffix}")
    shutil.copy(INPUT_EXERCISES_FILE, backup_file)


    with open(INPUT_EXERCISES_FILE, "r", encoding="utf-8") as f:
        exercises = json.load(f)

    # Add a derived filename for use by the browser.
    # This handles your first example where ".mp4" is missing.
    for exercise in exercises:
        video = exercise.get("video", "")

        if video and not video.lower().endswith(".mp4"):
            video += ".mp4"

        exercise["video_filename"] = video

        if gif_url := exercise.get("gif", None):
            exercise["gif_url"] = gif_url

        # Migrate the old flat "attributes" field to "movements".
        if "attributes" in exercise:
            exercise.setdefault("movements", exercise.pop("attributes"))

    return exercises


exercises = load_exercises()

# Easy lookup by exercise id
exercise_by_id = {
    exercise["id"]: exercise
    for exercise in exercises
}

# In-memory classification state.
#
# Initialize from the input JSON if it already has values.
# Selections are kept per category group so they can be saved
# back out as separate "movements" / "muscles" / "fitness" fields.
classification_state = {}

for exercise in exercises:
    classification_state[exercise["id"]] = {
        group: {
            flag: bool(exercise.get(group, {}).get(flag, False))
            for flag in info["flags"]
        }
        for group, info in CATEGORIES.items()
    }

def build_search_index(exercise):
    # Flattens an exercise's fields (plus its live checkbox groups) into
    # simple key -> string pairs so the client-side filter can do
    # substring matching on both attribute names and values.
    combined = {
        key: value
        for key, value in exercise.items()
        if key not in ("video_filename", "gif_url")
    }
    combined.update(classification_state[exercise["id"]])

    index = {}
    for key, value in combined.items():
        if isinstance(value, dict):
            index[key] = ", ".join(flag for flag, checked in value.items() if checked)
        elif isinstance(value, list):
            index[key] = ", ".join(str(v) for v in value)
        else:
            index[key] = "" if value is None else str(value)

    return index


@app.route("/")
def index():
    search_index = {
        exercise["id"]: build_search_index(exercise)
        for exercise in exercises
    }

    return render_template(
        "exercises.html",
        exercises=exercises,
        categories=CATEGORIES,
        classification_state=classification_state,
        search_index=search_index,
    )


@app.route("/videos/<path:filename>")
def video(filename):
    """
    Serve videos from /home/myvideos.
    """
    return send_from_directory(
        VIDEO_DIR,
        filename,
        conditional=True,
    )


@app.post("/exercise/<exercise_id>/group/<group>/flag/<flag>")
def update_flag(exercise_id, group, flag):

    if exercise_id not in exercise_by_id:
        return "Unknown exercise", 404

    if group not in CATEGORIES or flag not in CATEGORIES[group]["flags"]:
        return "Unknown flag", 400

    # Important:
    #
    # HTML checkboxes are only included in submitted form data
    # when they are checked.
    #
    # Since this request is triggered whenever the checkbox changes:
    #
    #     value present    -> checked
    #     value absent     -> unchecked
    #
    checked = "value" in request.form

    with state_lock:
        classification_state[exercise_id][group][flag] = checked

    print(
        f"{exercise_id}: {group}.{flag} = {checked}"
    )

    # HTMX doesn't need to replace anything on the page.
    return "", 204


@app.post("/save")
def save():

    output = []

    with state_lock:

        for exercise in exercises:

            # Don't save our internally generated helper field.
            item = {
                key: value
                for key, value in exercise.items()
                if key != "video_filename" and key != "gif_url"
            }
            item['origin'] = 'vimeo'
            for group in CATEGORIES:
                item[group] = dict(
                    classification_state[exercise["id"]][group]
                )

            output.append(item)

        
        with open(INPUT_EXERCISES_FILE, "w", encoding="utf-8") as f:
            json.dump(
                output,
                f,
                indent=2,
                ensure_ascii=False,
            )

    return f"""
        <div class="alert alert-success py-2 mb-0">
            Saved {len(output)} exercises to
            <strong>{INPUT_EXERCISES_FILE}</strong>
        </div>
    """


if __name__ == "__main__":
    # use_reloader=False is useful here because the Flask debug
    # reloader would reset the in-memory dictionary when it reloads.
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        use_reloader=False,
    )

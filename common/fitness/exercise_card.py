from flask import url_for


def extract_image_url(entity):
    if entity.get("gif"):
        return entity["gif"]
    images = entity.get("images")
    if isinstance(images, list) and images:
        return images[0].get("url")
    return None


def exercise_image(entity):
    return extract_image_url(entity) or url_for("static", filename="images/exercise.png")


def exercise_equipment(entity):
    equipment = entity.get("equipment_list")
    if equipment:
        return ", ".join(equipment)
    return entity.get("equipment")

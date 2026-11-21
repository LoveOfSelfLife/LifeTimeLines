from datetime import datetime
import logging

from flask import url_for


logger = logging.getLogger(__name__)


def program_image(entity):
    return url_for("static", filename="images/program.png")


def workout_image(entity):
    return url_for("static", filename="images/exercise_workout.png")


def member_name(entity):
    member_id = entity.get("assigned_to_member_id") or entity.get("member_id")
    if member_id:
        from common.member_entity import get_member_name_from_member_id
        return get_member_name_from_member_id(member_id)
    return None


def assigned_client_name(entity):
    member_id = entity.get("assigned_to_member_id")
    if member_id:
        from common.member_entity import get_member_name_from_member_id
        return get_member_name_from_member_id(member_id)
    return ""


def get_program_name_from_program_id(program_id):
    if not program_id:
        return None
    from common.entities_getter import get_entity
    from common.fitness.member_program_entity import MemberProgramsEntity
    program_entity = get_entity(MemberProgramsEntity.table_name, program_id)
    if program_entity:
        return program_entity.get("name")
    return None


def program_name(entity):
    program_id = entity.get("member_program_id")
    if program_id:
        return get_program_name_from_program_id(program_id)
    return None


def simple_date(date_str):
    if not date_str:
        return ""
    try:
        return datetime.fromisoformat(date_str).strftime("%Y-%m-%d")
    except (TypeError, ValueError) as e:
        logger.error("Error parsing date: %s", e)
        return ""


def workout_date(entity):
    return simple_date(entity.get("started_ts"))

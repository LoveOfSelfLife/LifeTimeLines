import logging
import uuid

from flask import abort, request

from common.auth import auth
from common.blueprint import create_blueprint
from common.fitness.exercise_history_analytics import (
    GROUP_BY_OPTIONS, METRIC_OPTIONS, RESOLUTION_OPTIONS,
    build_chart_json, exercise_events, group_events, load_member_history,
    summarize_exercises, summarize_groups, workout_rows)
from common.member_entity import get_member_id_from_user_context
from common.template_renderer import hx_render_template

logger = logging.getLogger(__name__)

bp = create_blueprint('exercise_history', __name__)


def _arg(name, options, default):
    value = request.args.get(name, default)
    return value if value in options else default


def _member_id(context):
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)
    return member_id


def _view_args():
    return {
        'group_by': _arg('group_by', GROUP_BY_OPTIONS, 'family'),
        'metric': _arg('metric', METRIC_OPTIONS, 'volume'),
        'resolution': _arg('resolution', RESOLUTION_OPTIONS, 'workout'),
        'group_by_options': GROUP_BY_OPTIONS,
        'metric_options': METRIC_OPTIONS,
        'resolution_options': RESOLUTION_OPTIONS,
    }


@bp.route('/')
@auth.login_required
def root(context=None):
    """the page; each visit also tops up the member's exercise history from any workouts not yet recorded"""
    member_id = _member_id(context)
    args = _view_args()
    df = load_member_history(member_id, sync=True)
    return hx_render_template('exercise_history/exercise_history.html',
                              groups=summarize_groups(df, args['group_by']),
                              context=context, **args)


@bp.route('/groups')
@auth.login_required
def groups(context=None):
    member_id = _member_id(context)
    args = _view_args()
    df = load_member_history(member_id)
    return hx_render_template('exercise_history/_groups.html',
                              groups=summarize_groups(df, args['group_by']),
                              context=context, **args)


@bp.route('/group')
@auth.login_required
def group_detail(context=None):
    member_id = _member_id(context)
    args = _view_args()
    group = request.args.get('group')
    if not group:
        abort(400, "No group provided")
    df = group_events(load_member_history(member_id), args['group_by'], group)
    return hx_render_template('exercise_history/_group_detail.html',
                              group=group,
                              exercises=summarize_exercises(df) if not df.empty else [],
                              chart_json=build_chart_json(df, args['metric'], args['resolution']),
                              chart_id=f"chart_{uuid.uuid4().hex[:8]}",
                              context=context, **args)


@bp.route('/exercise')
@auth.login_required
def exercise_detail(context=None):
    member_id = _member_id(context)
    args = _view_args()
    exercise_id = request.args.get('exercise_id')
    if not exercise_id:
        abort(400, "No exercise id provided")
    df = exercise_events(load_member_history(member_id), exercise_id)
    return hx_render_template('exercise_history/_exercise_detail.html',
                              exercise_id=exercise_id,
                              group=request.args.get('group', ''),
                              exercise_name=df['exercise_name'].iloc[0] if not df.empty else exercise_id,
                              workouts=workout_rows(df) if not df.empty else [],
                              chart_json=build_chart_json(df, args['metric'], args['resolution']),
                              chart_id=f"chart_{uuid.uuid4().hex[:8]}",
                              context=context, **args)

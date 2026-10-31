import logging
import uuid

from flask import abort, request

from common.auth import auth
from common.blueprint import create_blueprint
from common.fitness import exercise_analytics_db as adb
from common.fitness import exercise_analytics_queries as aq
from common.fitness.exercise_history_analytics import (
    GROUP_BY_OPTIONS, METRIC_OPTIONS, RESOLUTION_OPTIONS, build_chart_json, label_volumes, workout_rows)
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


def _connect(member_id, build=False):
    conn = adb.connect()
    if build:
        # the first time a member opens the page, their whole history is loaded from the entity store
        adb.ensure_member_built(conn, member_id)
    return conn


@bp.route('/')
@auth.login_required
def root(context=None):
    member_id = _member_id(context)
    args = _view_args()
    conn = _connect(member_id, build=True)
    try:
        groups = label_volumes(aq.group_summaries(conn, member_id, args['group_by']))
    finally:
        conn.close()
    return hx_render_template('exercise_history/exercise_history.html', groups=groups, context=context, **args)


@bp.route('/groups')
@auth.login_required
def groups(context=None):
    member_id = _member_id(context)
    args = _view_args()
    conn = _connect(member_id)
    try:
        groups = label_volumes(aq.group_summaries(conn, member_id, args['group_by']))
    finally:
        conn.close()
    return hx_render_template('exercise_history/_groups.html', groups=groups, context=context, **args)


@bp.route('/group')
@auth.login_required
def group_detail(context=None):
    member_id = _member_id(context)
    args = _view_args()
    group = request.args.get('group')
    if not group:
        abort(400, "No group provided")
    conn = _connect(member_id)
    try:
        exercises = label_volumes(aq.group_exercises(conn, member_id, args['group_by'], group))
        series = aq.time_series(conn, member_id, args['metric'], args['resolution'],
                                group_by=args['group_by'], group=group)
    finally:
        conn.close()
    return hx_render_template('exercise_history/_group_detail.html', group=group, exercises=exercises,
                              chart_json=build_chart_json(series, args['metric']),
                              chart_id=f"chart_{uuid.uuid4().hex[:8]}", context=context, **args)


@bp.route('/exercise')
@auth.login_required
def exercise_detail(context=None):
    member_id = _member_id(context)
    args = _view_args()
    exercise_id = request.args.get('exercise_id')
    if not exercise_id:
        abort(400, "No exercise id provided")
    conn = _connect(member_id)
    try:
        name = aq.exercise_name(conn, exercise_id)
        workouts = workout_rows(aq.exercise_history(conn, member_id, exercise_id))
        series = aq.time_series(conn, member_id, args['metric'], args['resolution'], exercise_id=exercise_id)
    finally:
        conn.close()
    return hx_render_template('exercise_history/_exercise_detail.html', exercise_id=exercise_id,
                              group=request.args.get('group', ''), exercise_name=name, workouts=workouts,
                              chart_json=build_chart_json(series, args['metric']),
                              chart_id=f"chart_{uuid.uuid4().hex[:8]}", context=context, **args)

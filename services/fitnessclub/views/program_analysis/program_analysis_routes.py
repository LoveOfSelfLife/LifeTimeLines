import json
import logging
import uuid

from flask import Response, abort, make_response, render_template, request

from common.auth import auth
from common.blueprint import create_blueprint
from common.entities_getter import filter_entities_by_member_role, get_entity, get_filtered_entities
from common.entity_store import EntityStore
from common.fitness.entity_constants import PROGRAM_ENTITY_NAME
from common.fitness.member_program_entity import MemberProgramsEntity
from common.fitness.program_analysis import export
from common.fitness.program_analysis.analyze import DEFAULT_SECONDARY_WEIGHT, analyze, expected_keys
from common.fitness.program_analysis.charts import build_charts
from common.fitness.program_analysis.extract import load_program_rows
from common.fitness.program_analysis.objectives import (
    BUILTIN_BALANCED_ID, DIMENSION_LABELS, METRICS, PURPOSES, ProgramObjectiveEntity, balanced_objective, evaluate,
    new_objective_record, validate_rules)
from common.member_entity import get_member_id_from_user_context, is_member_an_admin
from common.roles_service import is_member_coach
from common.template_renderer import hx_render_template

logger = logging.getLogger(__name__)

bp = create_blueprint('program_analysis', __name__)


def _member_id(context):
    member_id = get_member_id_from_user_context(context)
    if not member_id:
        abort(401)
    return member_id


def _load_program(member_id, program_id):
    program = get_entity(PROGRAM_ENTITY_NAME, program_id) if program_id else None
    if not program:
        abort(404, "Program not found")
    if not filter_entities_by_member_role(member_id, [{'key': program_id, 'entity': program}]):
        abort(403)
    return program


def _all_objectives():
    stored = [dict(e) for e in get_filtered_entities(ProgramObjectiveEntity.table_name)]
    return [balanced_objective()] + sorted(stored, key=lambda o: (o.get('name') or '').lower())


def _objective_by_id(objective_id):
    if not objective_id:
        return None
    if objective_id == BUILTIN_BALANCED_ID:
        return balanced_objective()
    entity = get_entity(ProgramObjectiveEntity.table_name, objective_id)
    return dict(entity) if entity else None


def _report_args(program):
    include_ramp = request.args.get('include_ramp') in ('1', 'true', 'on')
    objective_id = request.args.get('objective_id')
    if objective_id is None:
        applied = program.get('objective_ids') or []
        objective_id = applied[0] if applied else ''
    return include_ramp, objective_id


def _build_report(program, include_ramp, objective_id):
    infos, rows = load_program_rows(program)
    objective = _objective_by_id(objective_id)
    weight = (objective or {}).get('secondary_muscle_weight')
    weight = DEFAULT_SECONDARY_WEIGHT if weight in (None, '') else float(weight)
    analysis = analyze(infos, rows, include_ramp=include_ramp, secondary_weight=weight)
    evaluation = evaluate(analysis, objective) if objective else None
    return infos, rows, analysis, evaluation, objective


def _report_context(program, context=None):
    include_ramp, objective_id = _report_args(program)
    infos, rows, analysis, evaluation, objective = _build_report(program, include_ramp, objective_id)
    return dict(program=program, analysis=analysis, evaluation=evaluation, objective=objective,
                objective_id=objective_id or '', objectives=_all_objectives(), include_ramp=include_ramp,
                charts=build_charts(analysis, evaluation), context=context,
                applied_objective_ids=program.get('objective_ids') or [])


@bp.route('/report')
@auth.login_required
def report(context=None):
    # program_id may also be passed as a query parameter named 'key'
    # however key will set as the "composite_key" for the program
    # If 'key' is used, it should be treated as the composite key for the program.
    # extract the first element from the composite key if it exists
    program_key = request.args.get('key')
    program_id = request.args.get('program_id') or _get_key_from_composite_key(program_key)
    program = _load_program(_member_id(context), program_id)
    return hx_render_template('program_analysis/report.html', **_report_context(program, context))

def _get_key_from_composite_key(composite_key):
    if composite_key:
        try:
            composite_key = eval(composite_key)
            if isinstance(composite_key, (list, tuple)) and composite_key:
                return composite_key[0]
        except:
            pass
    return None

@bp.route('/print')
@auth.login_required
def print_view(context=None):
    program_key = request.args.get('key')
    program_id = request.args.get('program_id') or _get_key_from_composite_key(program_key)
    program = _load_program(_member_id(context), program_id)
    return render_template('program_analysis/print.html', **_report_context(program, context))


@bp.route('/export')
@auth.login_required
def export_report(context=None):
    program_key = request.args.get('key')
    program_id = request.args.get('program_id') or _get_key_from_composite_key(program_key)
    program = _load_program(_member_id(context), program_id)
    include_ramp, objective_id = _report_args(program)
    infos, rows, analysis, evaluation, _ = _build_report(program, include_ramp, objective_id)
    fmt = request.args.get('format', 'xlsx')
    base = ''.join(c if c.isalnum() or c in '-_' else '_' for c in (program.get('name') or 'program')) + '_analysis'
    if fmt == 'xlsx':
        body, mime = export.to_xlsx(export.sheets(analysis, infos, rows, evaluation)), \
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    elif fmt == 'csv':
        body, mime = export.to_csv(infos, rows), 'text/csv'
    elif fmt == 'json':
        body, mime = export.to_json(analysis, evaluation), 'application/json'
    else:
        abort(400, "Unknown export format")
    return Response(body, mimetype=mime, headers={'Content-Disposition': f'attachment; filename="{base}.{fmt}"'})


@bp.route('/apply', methods=['POST'])
@auth.login_required
def apply_objective(context=None):
    """records which objective the program is measured against, so the report opens with it selected"""
    program = _load_program(_member_id(context), request.form.get('program_id'))
    objective_id = request.form.get('objective_id') or ''
    if objective_id and not _objective_by_id(objective_id):
        abort(404, "Objective not found")
    program['objective_ids'] = [objective_id] if objective_id else []
    EntityStore().upsert_item(MemberProgramsEntity(program))
    response = make_response('', 204)
    response.headers['HX-Trigger'] = json.dumps({"showMessage": {"target": "body", "value": "Objective applied to program."}})
    return response


# ----- objectives library -----

def _can_manage(member_id):
    return is_member_coach(member_id) or is_member_an_admin(member_id)


def _can_edit(member_id, objective):
    return is_member_an_admin(member_id) or (_can_manage(member_id) and objective.get('created_by') == member_id)


def _key_options():
    return expected_keys(True)


def _new_id():
    return f"obj_{uuid.uuid4().hex[:12]}"


@bp.route('/objectives')
@auth.login_required
def objectives_listing(context=None):
    return objectives_listing2(context=context)

def objectives_listing2(context=None):
    member_id = _member_id(context)
    objectives = _all_objectives()
    editable = {o['id'] for o in objectives if not o.get('builtin') and _can_edit(member_id, o)}
    return hx_render_template('program_analysis/objectives_list.html', objectives=objectives,
                              can_manage=_can_manage(member_id), editable=editable, context=context)

@bp.route('/objectives/edit')
@auth.login_required
def objective_edit(context=None):
    member_id = _member_id(context)
    if not _can_manage(member_id):
        abort(403)
    objective_id = request.args.get('id')
    objective = _objective_by_id(objective_id) if objective_id else {
        'name': '', 'description': '', 'rules': [], 'secondary_muscle_weight': DEFAULT_SECONDARY_WEIGHT}
    if objective is None:
        abort(404)
    read_only = bool(objective_id) and (objective.get('builtin') or not _can_edit(member_id, objective))
    return hx_render_template('program_analysis/objective_edit.html', objective=objective, read_only=read_only,
                              dimensions=DIMENSION_LABELS, metrics=METRICS, purposes=PURPOSES,
                              key_options=_key_options(), context=context)


@bp.route('/objectives/save', methods=['POST'])
@auth.login_required
def objective_save(context=None):
    member_id = _member_id(context)
    if not _can_manage(member_id):
        abort(403)
    objective_id = request.form.get('id') or None
    existing = None
    if objective_id:
        if objective_id == BUILTIN_BALANCED_ID:
            abort(403)
        existing = get_entity(ProgramObjectiveEntity.table_name, objective_id)
        if not existing:
            abort(404)
        if not _can_edit(member_id, existing):
            abort(403)
    name = (request.form.get('name') or '').strip()
    try:
        rules = json.loads(request.form.get('rules_json') or '[]')
        weight = float(request.form.get('secondary_muscle_weight') or DEFAULT_SECONDARY_WEIGHT)
    except ValueError:
        abort(400, "Invalid objective")
    errors = validate_rules(rules)
    if not name:
        errors.append('A name is required.')
    if not 0 <= weight <= 1:
        errors.append('Secondary muscle weight must be between 0 and 1.')
    if errors:
        # htmx does not swap 4xx responses, so validation errors are returned as a normal response retargeted to the error box
        response = make_response('<div class="alert alert-danger">' + '<br>'.join(_esc(e) for e in errors) + '</div>')
        response.headers['HX-Retarget'] = '#objective-errors'
        response.headers['HX-Reswap'] = 'innerHTML'
        return response
    record = new_objective_record(name, (request.form.get('description') or '').strip(), rules, weight, member_id,
                                  dict(existing) if existing else None)
    if not existing:
        record['id'] = _new_id()
    EntityStore().upsert_item(ProgramObjectiveEntity(record))
    return objectives_listing2(context)


@bp.route('/objectives/copy', methods=['POST'])
@auth.login_required
def objective_copy(context=None):
    member_id = _member_id(context)
    if not _can_manage(member_id):
        abort(403)
    source = _objective_by_id(request.form.get('id'))
    if not source:
        abort(404)
    name = (request.form.get('name') or '').strip() or f"Copy of {source.get('name')}"
    record = new_objective_record(name, source.get('description') or '', source.get('rules') or [],
                                  source.get('secondary_muscle_weight') or DEFAULT_SECONDARY_WEIGHT, member_id)
    record['id'] = _new_id()
    EntityStore().upsert_item(ProgramObjectiveEntity(record))
    return objectives_listing2(context)


@bp.route('/objectives/delete', methods=['POST'])
@auth.login_required
def objective_delete(context=None):
    member_id = _member_id(context)
    objective_id = request.form.get('id')
    existing = get_entity(ProgramObjectiveEntity.table_name, objective_id) if objective_id else None
    if not existing:
        abort(404)
    if not _can_edit(member_id, existing):
        abort(403)
    EntityStore().delete_item(ProgramObjectiveEntity(dict(existing)))
    return objectives_listing2(context)


def _esc(text):
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

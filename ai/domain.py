"""Reviewed-candidate recommendation domain, independent of the AI provider.

The model can select only candidate IDs. All values, citations, and visible
explanations come from our reviewed catalogue, never model-generated prose.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / 'web/dist/recommendation-data.json').read_text())
OUTCOMES = {'a', 'b', 'equal', 'unsure', 'skip'}
EXPERIENCE_LIMIT = 300


def _signals(answers):
    return {f'{key}:{value}' for key, values in answers.items()
            for value in (values if isinstance(values, list) else [values])}


def _reason(matches):
    labels = [CATALOG['inputs'][s.split(':')[0]][s.split(':')[1]] for s in matches]
    return '‘' + '’, ‘'.join(labels) + '’를 선택한 응답을 참고했어요' if labels else '지금 설정을 유지하며 직접 비교할 수 있는 출발점이에요'


def _candidates(settings, signals, history, *, with_experience=False):
    candidates = []
    for action in CATALOG['actions']:
        matches = [s for s in action['matchAny'] if s in signals]
        if action['id'] != 'keep' and (
                (not matches and not with_experience)
                or any(s in signals for s in action['unlessAny'])
                or history.get(action['axis']) in {'a', 'b', 'equal', 'skip'}):
            continue
        changes = {}
        for key, op in action['adjust'].items():
            if 'set' in op:
                changes[key] = op['set']
            else:
                lo, hi = CATALOG['ranges'][key]
                changes[key] = max(lo, min(hi, settings[key] + op['delta']))
        reason = _reason(matches)
        if with_experience and not matches and action['id'] != 'keep':
            reason = '적은 문장을 참고해 고른 준비된 설정이에요'
        candidates.append({'id': action['id'], 'title': action['title'], 'axis': action['axis'], 'changes': changes,
                           'sourceIds': action['sources'], 'reason': reason})
    return candidates


def normalize_settings(raw):
    if not isinstance(raw, dict):
        raise ValueError('currentSettings must be an object')
    result = dict(CATALOG['defaults'])
    for key, limits in CATALOG['ranges'].items():
        value = raw.get(key)
        if type(value) in (int, float) and math.isfinite(value):
            result[key] = max(limits[0], min(limits[1], value))
    for key, default in CATALOG['defaults'].items():
        if type(default) is bool and type(raw.get(key)) is bool:
            result[key] = raw[key]
    if raw.get('profileId') in CATALOG['profiles']:
        result['profileId'] = raw['profileId']
    return result


def prepare(payload):
    if not isinstance(payload, dict) or set(payload) - {'currentSettings', 'answers', 'comparisons', 'useAI', 'experience'}:
        raise ValueError('Unsupported request fields')
    experience = payload.get('experience', '')
    if not isinstance(experience, str):
        raise ValueError('experience must be a string')
    experience = experience.strip()
    if len(experience) > EXPERIENCE_LIMIT:
        raise ValueError('experience exceeds the length limit')
    # Reject invalid Unicode without including the text in an error or log.
    try:
        experience.encode('utf-8')
    except UnicodeEncodeError:
        raise ValueError('Invalid experience encoding') from None
    settings = normalize_settings(payload.get('currentSettings', {}))
    raw_answers = payload.get('answers', {})
    if not isinstance(raw_answers, dict) or set(raw_answers) - set(CATALOG['inputs']):
        raise ValueError('Unsupported answer fields')
    if 'useAI' in payload and type(payload['useAI']) is not bool:
        raise ValueError('Invalid AI option')
    answers = {}
    for key, choices in CATALOG['inputs'].items():
        if key == 'concerns':
            values = raw_answers.get(key, [])
            if not isinstance(values, list) or len(values) > len(choices) or any(not isinstance(v, str) or v not in choices for v in values):
                raise ValueError('Invalid concerns')
            answers[key] = list(dict.fromkeys(values))
        else:
            value = raw_answers.get(key, next(iter(choices)))
            if not isinstance(value, str) or value not in choices:
                raise ValueError('Invalid answer')
            answers[key] = value
    signals = _signals(answers)
    history = {}
    comparisons = payload.get('comparisons', [])
    axes = {c['id'] for c in CATALOG['comparisons']}
    if not isinstance(comparisons, list) or len(comparisons) > 20:
        raise ValueError('Invalid comparisons')
    for item in comparisons:
        if not isinstance(item, dict) or set(item) != {'axis', 'outcome'} or not isinstance(item['axis'], str) or not isinstance(item['outcome'], str) or item['axis'] not in axes or item['outcome'] not in OUTCOMES:
            raise ValueError('Invalid comparison response')
        history[item['axis']] = item['outcome']

    candidates = _candidates(settings, signals, history)
    next_comparisons = []
    for item in CATALOG['comparisons']:
        if history.get(item['id']) in {'a', 'b', 'equal', 'skip'}:
            continue
        matches = [s for s in item['matchAny'] if s in signals]
        explanation = (_reason(matches) + ' ' if matches else '')
        explanation += '앞서 판단을 보류한 항목이라 원할 때 다시 비교할 수 있어요' if history.get(item['id']) == 'unsure' else '아직 선택하지 않은 항목이라 다음 비교 후보로 제안해요'
        next_comparisons.append({'id': item['id'], 'axis': item['id'], 'title': item['title'],
                                 'sourceIds': item['sources'], 'priority': 2 if matches else 0, 'reason': explanation})
    next_comparisons.sort(key=lambda item: -item['priority'])
    return {'settings': settings, 'answers': answers, 'experience': experience,
            'candidates': candidates, 'comparisons': next_comparisons,
            'history': [{'axis': axis, 'outcome': outcome} for axis, outcome in history.items()]}


def ai_plan(plan):
    """Expand reviewed choices for Claude only; the rule plan stays unchanged."""
    if not plan['experience']:
        return plan
    history = {item['axis']: item['outcome'] for item in plan['history']}
    known = {item['id'] for item in plan['candidates']}
    candidates = _candidates(plan['settings'], _signals(plan['answers']), history, with_experience=True)
    return {**plan, 'candidates': [{**item, 'matched': item['id'] in known} for item in candidates]}


def _mode_ids(plan, source):
    if source != 'ai' or not plan['experience'] or plan['answers']['goal'] == 'original':
        return ['keep']
    return ['keep'] + [mode['id'] for mode in CATALOG['startingModes'] if mode['id'] in CATALOG['profiles']]


def default_selection(plan):
    actions = [x['id'] for x in plan['candidates'] if x['id'] != 'keep'][:3]
    return {'actionIds': actions or ['keep'], 'nextComparisonId': plan['comparisons'][0]['id'] if plan['comparisons'] else 'done',
            'startingModeId': 'keep'}


def compose(plan, selection=None, source='rules', status='default'):
    selection = default_selection(plan) if selection is None else selection
    required = {'actionIds', 'nextComparisonId'}
    if not isinstance(selection, dict) or not required <= set(selection) or set(selection) - (required | {'startingModeId'}):
        raise ValueError('Invalid selection schema')
    if source == 'ai' and plan['experience'] and 'startingModeId' not in selection:
        raise ValueError('Missing starting mode')
    selection = {'startingModeId': 'keep', **selection}
    mode = selection['startingModeId']
    if not isinstance(mode, str) or mode not in _mode_ids(plan, source):
        raise ValueError('Starting mode was not offered')
    ids = selection['actionIds']
    if not isinstance(ids, list) or not 1 <= len(ids) <= 3 or any(not isinstance(x, str) for x in ids) or len(ids) != len(set(ids)) or ('keep' in ids and len(ids) != 1):
        raise ValueError('Invalid action IDs')
    available = {x['id']: x for x in plan['candidates']}
    if any(x not in available for x in ids):
        raise ValueError('Candidate was not offered')
    actions = [available[x] for x in ids]
    next_item = next((x for x in plan['comparisons'] if x['id'] == selection['nextComparisonId']), None)
    if next_item is None and not (selection['nextComparisonId'] == 'done' and not plan['comparisons']):
        raise ValueError('Comparison was not offered')
    settings = dict(plan['settings'])
    changes = {}
    for action in actions:
        for key, value in action['changes'].items():
            if key in changes and changes[key] != value:
                raise ValueError('Conflicting candidate changes')
            changes[key] = value
    settings.update(changes)
    if mode != 'keep':
        # A mode is a starting label, not permission to overwrite a user's preset.
        settings['profileId'] = mode
    starting_mode = next((item for item in CATALOG['startingModes'] if item['id'] == mode), None) if mode != 'keep' else None
    source_ids = list(dict.fromkeys([sid for a in actions for sid in a['sourceIds']] + (next_item['sourceIds'] if next_item else [])))
    return {'source': source, 'status': status, 'evidenceVersion': CATALOG['version'], 'selection': selection,
            'settings': normalize_settings(settings), 'actions': actions, 'nextComparison': next_item,
            'startingMode': starting_mode,
            'sources': [CATALOG['sources'][sid] for sid in source_ids], 'boundary': CATALOG['boundary']}


def output_schema(plan):
    return {'type': 'object', 'properties': {
        'actionIds': {'type': 'array', 'items': {'type': 'string', 'enum': [x['id'] for x in plan['candidates']]}, 'minItems': 1, 'maxItems': 3},
        'nextComparisonId': {'type': 'string', 'enum': [x['id'] for x in plan['comparisons']] or ['done']},
        'startingModeId': {'type': 'string', 'enum': _mode_ids(plan, 'ai')}},
        'required': ['actionIds', 'nextComparisonId', 'startingModeId'], 'additionalProperties': False}

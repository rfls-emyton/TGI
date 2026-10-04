"""Bind conditional probe refinement to a complete, recorded acquisition scope."""
from copy import deepcopy
from .identity import decode, encode
from .frame_engine import canonical
from .organization_snapshot import snapshot
from .role_work import RoleSearchBudget
from .incidence import _endpoint
from .witness_probe import verify_witness_probe


def _inputs(model, measurements, root, plan, acquisition, source, start, budget):
    if not isinstance(source, str) or not source.strip():
        raise ValueError('Acquisition source required')
    encode(source)
    if type(start) is not int or start < 0:
        raise ValueError('Nonnegative frame start required')
    view = snapshot(model)
    history = snapshot(acquisition)
    if not verify_witness_probe(view, measurements, root, plan):
        raise ValueError('Invalid probe plan')
    scope = []
    for sid, (frames, _) in sorted(history.episodes.items()):
        budget.consume()
        if not history._alive(sid):
            raise ValueError('Invalid acquisition evidence')
        scope.append(dict(source=sid, frames=list(map(decode, frames))))
    if source not in history.episodes:
        raise ValueError('Missing acquisition source')
    frames = history.episodes[source][0]
    if start + 2 >= len(frames):
        raise ValueError('Missing actual response')
    context = view.episodes[root['source']][0][root['frame']][root['start']:root['stop']]
    if frames[start] != context:
        raise ValueError('Wrong observed context')
    query = decode(frames[start + 1])
    if query not in plan['result']['requests']:
        raise ValueError('Unadmitted request')
    return history, frames, scope, query


def certify_witness_probe_feedback(model, measurements, root, plan, acquisition,
                                   source, start, *, max_search_steps=None):
    budget = RoleSearchBudget(max_search_steps)
    with budget.scope():
        history, frames, scope, query = _inputs(
            model, measurements, root, plan, acquisition, source, start, budget)
        response = [decode(frames[start + 2])]
        row = next(r for r in plan['requests'] if r['query'] == query)
        selected = []
        for group in row['groups']:
            budget.consume()
            if group['response'] == response:
                selected.extend(group['branches'])
        occurrences = []
        for i in range(start, start + 3):
            budget.consume()
            occurrences.append(_endpoint(history, source, (i, 0, len(frames[i]))))
        return dict(policy='recorded_witness_probe_feedback_v1', plan=deepcopy(plan),
                    source=source, start=start, acquisition=scope,
                    occurrences=occurrences, response=response,
                    result=dict(status='CONDITIONAL_REFINEMENT' if selected else
                                'UNMODELED_RESPONSE', branches=selected))


def verify_witness_probe_feedback(model, measurements, root, plan, acquisition,
                                  source, start, certificate, *, max_search_steps=None):
    budget = RoleSearchBudget(max_search_steps)
    with budget.scope():
        try:
            if not isinstance(certificate, dict) or set(certificate) != {
                'policy', 'plan', 'source', 'start', 'acquisition', 'occurrences',
                'response', 'result'}:
                return False
            if (certificate['policy'] != 'recorded_witness_probe_feedback_v1' or
                certificate['source'] != source or type(certificate['start']) is not int or
                certificate['start'] != start or canonical(certificate['plan']) != canonical(plan)):
                return False
            history, frames, scope, query = _inputs(
                model, measurements, root, plan, acquisition, source, start, budget)
            if canonical(certificate['acquisition']) != canonical(scope):
                return False
            receipts = history.episodes[source][1]
            points = []
            for i in range(start, start + 3):
                budget.consume()
                origin = receipts[i].origin
                n = len(frames[i])
                offset = sum(map(len, frames[:i]))
                points.append(dict(frame=i, start=0, stop=n, event_span=[offset, offset+n],
                                   identities=list(frames[i]),
                                   coordinates=[[origin[0]+j, *origin[1:]] for j in range(n)]))
            response = [decode(frames[start + 2])]
            row = next(r for r in plan['requests'] if r['query'] == query)
            selected = []
            for i, branch in enumerate(row['certificate']['branches']):
                budget.consume()
                result = branch['response']['result']
                if result['status'] in ('CONDITIONAL_FUNCTION', 'OBSERVED_RESPONSE') and result['output'] == response:
                    selected.append(i)
            expected = dict(status='CONDITIONAL_REFINEMENT' if selected else
                            'UNMODELED_RESPONSE', branches=selected)
            return (canonical(certificate['occurrences']) == canonical(points) and
                    canonical(certificate['response']) == canonical(response) and
                    canonical(certificate['result']) == canonical(expected))
        except (KeyError, IndexError, TypeError, ValueError, AttributeError, StopIteration):
            return False

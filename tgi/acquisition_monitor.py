"""Stationary candidate monitoring over complete recorded acquisition histories."""
from copy import deepcopy
from tgi.identity import decode
from tgi.organization_snapshot import snapshot
from tgi.separation_check import verify_separating_requests

def _monitor(model, plan, acquisition, source, boundaries, budget):
    model = snapshot(model)
    plan = deepcopy(plan)
    if not verify_separating_requests(model, plan):
        raise ValueError('Invalid external plan')
    view = snapshot(acquisition)
    if not isinstance(source, str) or not source or source not in view.episodes:
        raise ValueError('Missing acquisition source')
    scope = []
    for sid, (raw, _) in sorted(view.episodes.items()):
        budget.consume()
        if not view._alive(sid):
            raise ValueError('Broken acquisition evidence')
        scope.append(dict(source=sid, frames=list(map(decode, raw))))
    frames, receipts = view.episodes[source]
    if not isinstance(boundaries, (list, tuple)) or len(boundaries) < 2 or any((type(x) is not int for x in boundaries)) or (boundaries[0] != 0) or (boundaries[-1] != len(frames)) or any((b - a < 2 for a, b in zip(boundaries, boundaries[1:]))):
        raise ValueError('Boundaries must cover every source frame')
    offsets = [0]
    for frame in frames:
        budget.consume()
        offsets.append(offsets[-1] + len(frame))
    universe = set(range(len(plan['contexts'])))
    possible, definite = (set(universe), set(universe))
    events = []
    for step, (start, stop) in enumerate(zip(boundaries, boundaries[1:])):
        budget.consume()
        request = decode(frames[start])
        observed = list(map(decode, frames[start + 1:stop]))
        if step == 0:
            if request != plan['request'] or observed != plan['observed']:
                raise ValueError('Initial observation differs from external plan')
            supported, unknown = (set(universe), set())
        else:
            row = next((r for r in plan['requests'] if r['query'] == request), None)
            groups = row['responses'] if row else []
            covered = set().union(*(set(g['contexts']) for g in groups))
            supported = set().union(*(set(g['contexts']) for g in groups if g['value'] == observed))
            unknown = universe - covered
            possible &= supported | unknown
            definite &= supported
        points = []
        for i in range(start, stop):
            budget.consume()
            origin = receipts[i].origin
            n = len(frames[i])
            points.append(dict(frame=i, start=0, stop=n,
                               event_span=[offsets[i], offsets[i+1]],
                               identities=list(frames[i]),
                               coordinates=[[origin[0]+j, *origin[1:]] for j in range(n)]))
        events.append(dict(request=request, observed=observed, supported=sorted(supported), unknown=sorted(unknown), possible=sorted(possible), definite=sorted(definite), occurrences=points))
    status = 'CONTRADICTED' if not possible else 'INCOMPLETE' if possible != definite else 'CONSISTENT'
    return dict(policy='stationary_acquisition_monitor_v1', plan=plan, source=source, scope=scope, boundaries=list(boundaries), events=events, result=dict(status=status, possible=sorted(possible), definite=sorted(definite)))

from tgi.role_work import RoleSearchBudget

def certify_acquisition_monitor(model, plan, acquisition, source, boundaries, *, max_search_steps=None):
    budget = RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        return _monitor(model, plan, acquisition, source, boundaries, budget)

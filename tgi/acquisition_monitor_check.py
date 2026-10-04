"""Independent candidate-wise verification, never invokes monitor producer."""
from tgi.identity import decode
from tgi.frame_engine import canonical
from tgi.organization_snapshot import snapshot
from tgi.separation_check import verify_separating_requests

def _verify_monitor(model, plan, acquisition, source, boundaries, c, budget):
    try:
        if not isinstance(c, dict) or set(c) != {'policy', 'plan', 'source', 'scope', 'boundaries', 'events', 'result'}:
            return False
        if c['policy'] != 'stationary_acquisition_monitor_v1' or c['source'] != source or canonical(c['plan']) != canonical(plan):
            return False
        model = snapshot(model)
        if not verify_separating_requests(model, plan):
            return False
        a = snapshot(acquisition)
        if not isinstance(source, str) or not source or source not in a.episodes:
            return False
        scope = []
        for sid, (raw, _) in sorted(a.episodes.items()):
            budget.consume()
            if not a._alive(sid):
                return False
            scope.append(dict(source=sid, frames=list(map(decode, raw))))
        if canonical(c['scope']) != canonical(scope):
            return False
        frames, receipts = a.episodes[source]
        if not isinstance(boundaries, (list, tuple)) or len(boundaries) < 2 or any((type(x) is not int for x in boundaries)) or (boundaries[0] != 0) or (boundaries[-1] != len(frames)) or any((b - a < 2 for a, b in zip(boundaries, boundaries[1:]))):
            return False
        if canonical(c['boundaries']) != canonical(list(boundaries)) or not isinstance(c['events'], list) or len(c['events']) != len(boundaries) - 1:
            return False
        verdicts = [[0, 0] for _ in plan['contexts']]
        offset = 0
        for step, (lo, hi) in enumerate(zip(boundaries, boundaries[1:])):
            budget.consume()
            query = decode(frames[lo])
            observed = [decode(frames[i]) for i in range(lo + 1, hi)]
            supported = []
            unknown = []
            if step == 0:
                if query != plan['request'] or observed != plan['observed']:
                    return False
                supported = list(range(len(verdicts)))
            else:
                for index, history in enumerate(verdicts):
                    budget.consume()
                    values = [g['value'] for row in plan['requests'] if row['query'] == query for g in row['responses'] if index in g['contexts']]
                    if not values:
                        unknown.append(index)
                        history[1] += 1
                    elif observed in values:
                        supported.append(index)
                    else:
                        history[0] += 1
            possible = [i for i, vs in enumerate(verdicts) if vs[0] == 0]
            definite = [i for i, vs in enumerate(verdicts) if vs == [0, 0]]
            points = []
            for i in range(lo, hi):
                budget.consume()
                n = len(frames[i])
                origin = receipts[i].origin
                points.append(dict(frame=i, start=0, stop=n, event_span=[offset, offset + n], identities=list(frames[i]), coordinates=[[origin[0] + j, *origin[1:]] for j in range(n)]))
                offset += n
            expected = dict(request=query, observed=observed, supported=supported, unknown=unknown, possible=possible, definite=definite, occurrences=points)
            if canonical(c['events'][step]) != canonical(expected):
                return False
        status = 'CONTRADICTED' if not possible else 'INCOMPLETE' if possible != definite else 'CONSISTENT'
        return canonical(c['result']) == canonical(dict(status=status, possible=possible, definite=definite))
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        return False

from tgi.role_work import RoleSearchBudget

def verify_acquisition_monitor(model, plan, acquisition, source, boundaries, certificate, *, max_search_steps=None):
    budget = RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        return _verify_monitor(model, plan, acquisition, source, boundaries, certificate, budget)

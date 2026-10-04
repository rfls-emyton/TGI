from copy import deepcopy
from tgi.acquisition_monitor_check import verify_acquisition_monitor
from tgi.compact_measured_path import _decimal_count

def _spectrum(model, plan, acquisition, source, boundaries, monitor, budget):
    if not verify_acquisition_monitor(model, plan, acquisition, source, boundaries, monitor):
        raise ValueError('Invalid monitored acquisition')
    monitor = deepcopy(monitor)
    n = len(plan['contexts'])
    events = monitor['events']
    states = [(0, -1, 0, 0, 0)]
    counts = [1]
    lookup = {states[0]: 0}
    edges = []
    cursor = 0
    while cursor < len(states):
        budget.consume()
        step, last, changes, incompatible, unknown = states[cursor]
        if step < len(events):
            event = events[step]
            for candidate in range(n):
                budget.consume()
                missing = candidate in event['unknown']
                mismatch = not missing and candidate not in event['supported']
                key = (step + 1, candidate, changes + int(last != -1 and last != candidate), incompatible + int(mismatch), unknown + int(missing))
                if key not in lookup:
                    lookup[key] = len(states)
                    states.append(key)
                    counts.append(0)
                target = lookup[key]
                counts[target] += counts[cursor]
                edges.append([cursor, target, candidate])
        cursor += 1
    terminals = [i for i, state in enumerate(states) if state[0] == len(events)]
    bins = {}
    for index in terminals:
        budget.consume()
        state = states[index]
        key = state[2:]
        if key not in bins:
            bins[key] = [0, []]
        bins[key][0] += counts[index]
        bins[key][1].append(index)
    histogram = [dict(changes=k[0], incompatible=k[1], unknown=k[2], count=_decimal_count(v[0]), terminals=v[1]) for k, v in sorted(bins.items())]
    possible = sorted((states[i][1] for i in terminals if states[i][2] == states[i][3] == 0))
    definite = sorted((states[i][1] for i in terminals if states[i][2] == states[i][3] == states[i][4] == 0))
    return dict(policy='temporal_candidate_spectrum_v1', monitor=monitor, nodes=[dict(step=s[0], last=s[1], changes=s[2], incompatible=s[3], unknown=s[4], count=_decimal_count(counts[i])) for i, s in enumerate(states)], edges=edges, terminals=terminals, histogram=histogram, total=_decimal_count(sum((counts[i] for i in terminals))), stationary=dict(possible=possible, definite=definite), answer=None)

from copy import deepcopy
from tgi.organization_snapshot import snapshot
from tgi.role_work import RoleSearchBudget

def certify_temporal_candidate_spectrum(model, plan, acquisition, source, boundaries, monitor, *, max_search_steps=None):
    budget = RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        return _spectrum(snapshot(model), deepcopy(plan), snapshot(acquisition), source, deepcopy(boundaries), deepcopy(monitor), budget)

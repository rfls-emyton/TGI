from tgi.acquisition_witness import certify_acquisition_witness
from tgi.organization_snapshot import snapshot
from tgi.compact_measured_path import _decimal_count

def _inputs(acquisition, source, boundaries, measurements, budget):
    view = snapshot(acquisition)
    if not isinstance(source, str) or not source or source not in view.episodes:
        raise ValueError('Missing acquisition source')
    frames = view.episodes[source][0]
    if not isinstance(boundaries, (list, tuple)) or len(boundaries) < 2 or any((type(x) is not int for x in boundaries)) or (boundaries[0] != 0) or (boundaries[-1] != len(frames)) or any((b - a < 2 for a, b in zip(boundaries, boundaries[1:]))):
        raise ValueError('Complete intervals required')
    witness = certify_acquisition_witness(view, measurements)
    expected = [stop - 1 for stop in boundaries[1:]]
    if len(measurements) != len(expected) or {r['frame'] for r in measurements} != set(expected) or any((r['source'] != source or r['start'] != 0 or r['stop'] != len(frames[r['frame']]) for r in measurements)):
        raise ValueError('Exactly one measured final response per event required')
    lookup = {r['frame']: r for r in witness['measurements']}
    records = [dict(lookup[frame]) for frame in expected]
    return (witness, records)

def _produce(acquisition, source, boundaries, measurements, budget):
    witness, records = _inputs(acquisition, source, boundaries, measurements, budget)
    base = dict(policy='response_interval_order_v1', source=source, boundaries=list(boundaries), witness=witness, responses=records)
    if len({r['clock'] for r in records}) != 1:
        return dict(**base, status='CLOCK_UNDETERMINED', precedence=[], nodes=[], edges=[], terminal=None, total=None, arrival_order_admissible=None)
    n = len(records)
    precedence = [[i, j] for i, a in enumerate(records) for j, b in enumerate(records) if i != j and a['upper'] < b['lower']]
    predecessors = [sum((1 << i for i, j in precedence if j == k)) for k in range(n)]
    masks = [0]
    lookup = {0: 0}
    counts = [1]
    edges = []
    cursor = 0
    while cursor < len(masks):
        budget.consume()
        mask = masks[cursor]
        for event in range(n):
            budget.consume()
            if mask & 1 << event or predecessors[event] & mask != predecessors[event]:
                continue
            next_mask = mask | 1 << event
            if next_mask not in lookup:
                lookup[next_mask] = len(masks)
                masks.append(next_mask)
                counts.append(0)
            target = lookup[next_mask]
            counts[target] += counts[cursor]
            edges.append([cursor, target, event])
        cursor += 1
    terminal = lookup[(1 << n) - 1]
    return dict(**base, status='TIME_COMPATIBLE_ORDERS', precedence=precedence, nodes=[dict(mask=mask, count=_decimal_count(counts[i])) for i, mask in enumerate(masks)], edges=edges, terminal=terminal, total=_decimal_count(counts[terminal]), arrival_order_admissible=all((i < j for i, j in precedence)))

from copy import deepcopy
from tgi.role_work import RoleSearchBudget

def certify_response_interval_order(acquisition, source, boundaries, measurements, *, max_search_steps=None):
    budget = RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        return _produce(snapshot(acquisition), source, deepcopy(boundaries), deepcopy(measurements), budget)

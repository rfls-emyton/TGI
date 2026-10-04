from tgi.acquisition_witness import verify_acquisition_witness
from tgi.organization_snapshot import snapshot
from tgi.compact_measured_path import _decimal_count
from tgi.frame_engine import canonical

def _verify(acquisition, source, boundaries, measurements, c, budget):
    try:
        fields = {'policy', 'source', 'boundaries', 'witness', 'responses', 'status', 'precedence', 'nodes', 'edges', 'terminal', 'total', 'arrival_order_admissible'}
        if not isinstance(c, dict) or set(c) != fields or c['policy'] != 'response_interval_order_v1' or (c['source'] != source) or (canonical(c['boundaries']) != canonical(list(boundaries))):
            return False
        v = snapshot(acquisition)
        if not isinstance(source, str) or not source or source not in v.episodes:
            return False
        frames = v.episodes[source][0]
        if not isinstance(boundaries, (list, tuple)) or len(boundaries) < 2 or any((type(x) is not int for x in boundaries)) or (boundaries[0] != 0) or (boundaries[-1] != len(frames)) or any((b - a < 2 for a, b in zip(boundaries, boundaries[1:]))):
            return False
        if not verify_acquisition_witness(v, measurements, c['witness']):
            return False
        finals = [stop - 1 for stop in boundaries[1:]]
        if len(measurements) != len(finals) or {r['frame'] for r in measurements} != set(finals):
            return False
        if any((r['source'] != source or r['start'] != 0 or r['stop'] != len(frames[r['frame']]) for r in measurements)):
            return False
        records = [next((dict(r) for r in measurements if r['frame'] == frame)) for frame in finals]
        if canonical(c['responses']) != canonical(records):
            return False
        if len({r['clock'] for r in records}) != 1:
            return c['status'] == 'CLOCK_UNDETERMINED' and c['precedence'] == [] and (c['nodes'] == []) and (c['edges'] == []) and (c['terminal'] is None) and (c['total'] is None) and (c['arrival_order_admissible'] is None)
        if c['status'] != 'TIME_COMPATIBLE_ORDERS':
            return False
        n = len(records)
        precedes = []
        required = [set() for _ in records]
        for i in range(n):
            budget.consume()
            for j in range(n):
                budget.consume()
                if i != j and records[i]['upper'] < records[j]['lower']:
                    precedes.append([i, j])
                    required[j].add(i)
        if canonical(c['precedence']) != canonical(precedes):
            return False
        masks = []
        lookup = {}
        for index, node in enumerate(c['nodes']):
            budget.consume()
            if set(node) != {'mask', 'count'} or type(node['mask']) is not int or (not 0 <= node['mask'] < 1 << n) or (node['mask'] in lookup):
                return False
            masks.append(node['mask'])
            lookup[node['mask']] = index
        if not masks or masks[0] != 0:
            return False
        incoming = [[] for _ in masks]
        edges = []
        for index, mask in enumerate(masks):
            budget.consume()
            present = {event for event in range(n) if mask & 1 << event}
            for event in range(n):
                budget.consume()
                if event in present or not required[event] <= present:
                    continue
                successor = mask | 1 << event
                if successor not in lookup:
                    return False
                target = lookup[successor]
                edges.append([index, target, event])
                incoming[target].append(index)
        if canonical(c['edges']) != canonical(edges):
            return False
        counts = [0] * len(masks)
        counts[0] = 1
        for i in sorted(range(1, len(masks)), key=lambda i: masks[i].bit_count()):
            budget.consume()
            counts[i] = sum((counts[j] for j in incoming[i]))
        if any((value == 0 for value in counts)) or any((node['count'] != _decimal_count(counts[i]) for i, node in enumerate(c['nodes']))):
            return False
        terminal = lookup[(1 << n) - 1]
        return type(c['terminal']) is int and c['terminal'] == terminal and (c['total'] == _decimal_count(counts[terminal])) and (type(c['arrival_order_admissible']) is bool) and (c['arrival_order_admissible'] == all((i < j for i, j in precedes)))
    except (KeyError, IndexError, TypeError, ValueError, AttributeError, StopIteration):
        return False

from copy import deepcopy
from tgi.role_work import RoleSearchBudget

def verify_response_interval_order(acquisition, source, boundaries, measurements, certificate, *, max_search_steps=None):
    budget = RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            return _verify(snapshot(acquisition), source, deepcopy(boundaries), deepcopy(measurements), certificate, budget)
        except (ValueError, TypeError, KeyError, AttributeError):
            return False

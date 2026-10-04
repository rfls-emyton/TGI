from tgi.acquisition_monitor_check import verify_acquisition_monitor
from tgi.compact_measured_path import _decimal_count
from tgi.frame_engine import canonical

def _verify_spectrum(model, plan, acquisition, source, boundaries, monitor, c, budget):
    try:
        if not isinstance(c, dict) or set(c) != {'policy', 'monitor', 'nodes', 'edges', 'terminals', 'histogram', 'total', 'stationary', 'answer'}:
            return False
        if c['policy'] != 'temporal_candidate_spectrum_v1' or c['answer'] is not None or canonical(c['monitor']) != canonical(monitor):
            return False
        if not verify_acquisition_monitor(model, plan, acquisition, source, boundaries, monitor):
            return False
        events = monitor['events']
        n = len(plan['contexts'])
        keys = []
        lookup = {}
        for index, node in enumerate(c['nodes']):
            budget.consume()
            if set(node) != {'step', 'last', 'changes', 'incompatible', 'unknown', 'count'}:
                return False
            key = tuple((node[field] for field in ('step', 'last', 'changes', 'incompatible', 'unknown')))
            if any((type(x) is not int for x in key)):
                return False
            step, last, changes, incompatible, unknown = key
            if not 0 <= step <= len(events) or not 0 <= changes <= max(0, step - 1) or (not 0 <= incompatible <= step) or (not 0 <= unknown <= step):
                return False
            if (last != -1 if step == 0 else not 0 <= last < n) or key in lookup:
                return False
            keys.append(key)
            lookup[key] = index
        if not keys or keys[0] != (0, -1, 0, 0, 0):
            return False
        local = []
        for step, event in enumerate(events):
            budget.consume()
            labels = []
            for candidate in range(n):
                budget.consume()
                values = [g['value'] for row in plan['requests'] if row['query'] == event['request'] for g in row['responses'] if candidate in g['contexts']]
                labels.append((0, 0) if step == 0 else (0, 1) if not values else (int(event['observed'] not in values), 0))
            local.append(labels)
        expected = []
        incoming = [[] for _ in keys]
        for index, (step, last, changes, incompatible, unknown) in enumerate(keys):
            budget.consume()
            if step == len(events):
                continue
            for candidate in range(n):
                budget.consume()
                mismatch, missing = local[step][candidate]
                successor = (step + 1, candidate, changes + (last != -1 and last != candidate), incompatible + mismatch, unknown + missing)
                if successor not in lookup:
                    return False
                target = lookup[successor]
                expected.append([index, target, candidate])
                incoming[target].append(index)
        if canonical(c['edges']) != canonical(expected):
            return False
        counts = [0] * len(keys)
        counts[0] = 1
        for index in sorted(range(1, len(keys)), key=lambda i: keys[i][0]):
            budget.consume()
            counts[index] = sum((counts[j] for j in incoming[index]))
        if any((value == 0 for value in counts)) or any((node['count'] != _decimal_count(counts[i]) for i, node in enumerate(c['nodes']))):
            return False
        terminals = [i for i, key in enumerate(keys) if key[0] == len(events)]
        if canonical(c['terminals']) != canonical(terminals):
            return False
        grouped = {}
        for index in terminals:
            budget.consume()
            key = keys[index][2:]
            value, provenance = grouped.setdefault(key, [0, []])
            grouped[key][0] += counts[index]
            provenance.append(index)
        histogram = [dict(changes=k[0], incompatible=k[1], unknown=k[2], count=_decimal_count(value), terminals=ids) for k, (value, ids) in sorted(grouped.items())]
        possible = [keys[i][1] for i in terminals if keys[i][2] == keys[i][3] == 0]
        definite = [keys[i][1] for i in terminals if keys[i][2] == keys[i][3] == keys[i][4] == 0]
        return canonical(c['histogram']) == canonical(histogram) and c['total'] == _decimal_count(sum((counts[i] for i in terminals))) and (canonical(c['stationary']) == canonical(dict(possible=sorted(possible), definite=sorted(definite))))
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        return False

from copy import deepcopy
from tgi.organization_snapshot import snapshot
from tgi.role_work import RoleSearchBudget

def verify_temporal_candidate_spectrum(model, plan, acquisition, source, boundaries, monitor, certificate, *, max_search_steps=None):
    budget = RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            return _verify_spectrum(snapshot(model), deepcopy(plan), snapshot(acquisition), source, deepcopy(boundaries), deepcopy(monitor), certificate, budget)
        except (ValueError, TypeError, KeyError, AttributeError):
            return False

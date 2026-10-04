from tgi.compact_measured_path import _decimal_count
from tgi.organization_snapshot import snapshot
from tgi.measured_capacity import verify_measured_capacity
from tgi.frame_engine import canonical

def _verify(model, records, left, right, c, budget):
    try:
        if set(c) != {'time', 'graphs', 'functional_capacity', 'deficit', 'status'}:
            return False
        m = snapshot(model)
        if not verify_measured_capacity(m, records, left, right, c['time']):
            return False
        if c['time']['status'] == 'CLOCK_UNDETERMINED':
            return c['graphs'] == [] and c['functional_capacity'] is None and (c['deficit'] is None) and (c['status'] == 'CLOCK_UNDETERMINED')
        left = sorted(left)
        right = sorted(right)
        compatible = set(map(tuple, c['time']['edges']))
        histograms = []
        if len(c['graphs']) != 2:
            return False
        for graph, sign in zip(c['graphs'], (-1, 1)):
            budget.consume()
            if set(graph) != {'direction', 'nodes', 'edges', 'terminals', 'histogram'} or type(graph['direction']) is not int or graph['direction'] != sign:
                return False
            keys = []
            lookup = {}
            for index, node in enumerate(graph['nodes']):
                budget.consume()
                if set(node) != {'prefix', 'mask', 'relation', 'count'} or type(node['prefix']) is not int or type(node['mask']) is not int:
                    return False
                prefix, mask = (node['prefix'], node['mask'])
                items = tuple(map(tuple, node['relation']))
                if not 0 <= prefix <= len(left) or not 0 <= mask < 1 << len(right) or mask.bit_count() > prefix:
                    return False
                if any((len(p) != 2 or any((type(x) is not int for x in p)) for p in items)) or items != tuple(sorted(set(items))) or len({x for x, y in items}) != len(items):
                    return False
                key = (prefix, mask, items)
                if key in lookup:
                    return False
                keys.append(key)
                lookup[key] = index
            if not keys or keys[0] != (0, 0, ()):
                return False
            expected = []
            for source, (prefix, mask, items) in enumerate(keys):
                budget.consume()
                if prefix == len(left):
                    continue
                skip = (prefix + 1, mask, items)
                if skip not in lookup:
                    return False
                expected.append([source, lookup[skip], -1])
                for j, target in enumerate(right):
                    budget.consume()
                    if mask & 1 << j or (left[prefix], target) not in compatible:
                        continue
                    a = m.episodes[left[prefix]][0][0]
                    b = m.episodes[target][0][0]
                    if len(a) != len(b):
                        continue
                    pairs = set(items)
                    for k, y in enumerate(b):
                        budget.consume()
                        pairs.add((a[k if sign == 1 else len(a) - 1 - k], y))
                    if len({x for x, y in pairs}) != len(pairs):
                        continue
                    key = (prefix + 1, mask | 1 << j, tuple(sorted(pairs)))
                    if key not in lookup:
                        return False
                    expected.append([source, lookup[key], j])
            if canonical(graph['edges']) != canonical(expected):
                return False
            incoming = [[] for _ in keys]
            for a, b, _ in expected:
                budget.consume()
                incoming[b].append(a)
            counts = [0] * len(keys)
            counts[0] = 1
            for i in sorted(range(1, len(keys)), key=lambda i: keys[i][0]):
                budget.consume()
                counts[i] = sum((counts[j] for j in incoming[i]))
            if any((v == 0 for v in counts)) or any((node['count'] != _decimal_count(counts[i]) for i, node in enumerate(graph['nodes']))):
                return False
            terminals = [i for i, key in enumerate(keys) if key[0] == len(left)]
            if canonical(terminals) != canonical(graph['terminals']):
                return False
            histogram = {}
            for i in terminals:
                budget.consume()
                k = keys[i][1].bit_count()
                histogram[k] = histogram.get(k, 0) + counts[i]
            histogram = {str(k): _decimal_count(v) for k, v in histogram.items()}
            if canonical(histogram) != canonical(graph['histogram']):
                return False
            histograms.append(histogram)
        maximum = max((int(k) for h in histograms for k in h))
        deficit = c['time']['capacity_certificate']['capacity'] - maximum
        return type(c['functional_capacity']) is int and type(c['deficit']) is int and (c['functional_capacity'] == maximum) and (c['deficit'] == deficit) and (c['status'] == ('FUNCTIONAL_DEFICIT' if deficit else 'CAPACITY_ATTAINABLE'))
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        return False

from tgi.role_work import RoleSearchBudget
from tgi.measured_capacity import _copy_inputs

def verify_functional_capacity(model,records,left,right,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        try:r,a,b=_copy_inputs(records,left,right)
        except (ValueError,TypeError):return False
        return _verify(model,r,a,b,certificate,budget)

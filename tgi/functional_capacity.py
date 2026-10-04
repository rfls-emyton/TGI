from tgi.compact_measured_path import _decimal_count
from tgi.organization_snapshot import snapshot
from tgi.measured_capacity import certify_measured_capacity

def _produce(model, records, left, right, budget):
    m = snapshot(model)
    time = certify_measured_capacity(m, records, left, right)
    left = time['left']
    right = time['right']
    edges = set(map(tuple, time['edges']))
    graphs = []
    if time['status'] == 'CLOCK_UNDETERMINED':
        return dict(time=time, graphs=[], functional_capacity=None, deficit=None, status='CLOCK_UNDETERMINED')
    for sign in (-1, 1):
        budget.consume()
        states = [(0, 0, ())]
        lookup = {states[0]: 0}
        counts = [1]
        transitions = []
        cursor = 0
        while cursor < len(states):
            budget.consume()
            i, mask, items = states[cursor]
            if i < len(left):
                continuations = [(i + 1, mask, items, -1)]
                for j, b in enumerate(right):
                    budget.consume()
                    if mask & 1 << j or (left[i], b) not in edges:
                        continue
                    a = m.episodes[left[i]][0][0]
                    y = m.episodes[b][0][0]
                    if len(a) != len(y):
                        continue
                    mapping = dict(items)
                    valid = True
                    for k, u in enumerate(a):
                        budget.consume()
                        v = y[k if sign == 1 else len(a) - 1 - k]
                        if u in mapping and mapping[u] != v:
                            valid = False
                            break
                        mapping[u] = v
                    if valid:
                        continuations.append((i + 1, mask | 1 << j, tuple(sorted(mapping.items())), j))
                for ni, nm, relation, j in continuations:
                    budget.consume()
                    key = (ni, nm, relation)
                    if key not in lookup:
                        lookup[key] = len(states)
                        states.append(key)
                        counts.append(0)
                    target = lookup[key]
                    counts[target] += counts[cursor]
                    transitions.append([cursor, target, j])
            cursor += 1
        terminals = [i for i, s in enumerate(states) if s[0] == len(left)]
        histogram = {}
        for i in terminals:
            budget.consume()
            cardinality = states[i][1].bit_count()
            histogram[cardinality] = histogram.get(cardinality, 0) + counts[i]
        graphs.append(dict(direction=sign, nodes=[dict(prefix=i, mask=mask, relation=[list(p) for p in items], count=_decimal_count(counts[k])) for k, (i, mask, items) in enumerate(states)], edges=transitions, terminals=terminals, histogram={str(k): _decimal_count(v) for k, v in sorted(histogram.items())}))
    maximum = max((int(k) for g in graphs for k in g['histogram']))
    deficit = time['capacity_certificate']['capacity'] - maximum
    return dict(time=time, graphs=graphs, functional_capacity=maximum, deficit=deficit, status='FUNCTIONAL_DEFICIT' if deficit else 'CAPACITY_ATTAINABLE')

from tgi.role_work import RoleSearchBudget
from tgi.measured_capacity import _copy_inputs

def certify_functional_capacity(model,records,left,right,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        r,a,b=_copy_inputs(records,left,right)
        return _produce(snapshot(model),r,a,b,budget)

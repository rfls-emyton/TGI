"""All measured endpoint interleavings of raw before/action/after occurrences."""
from copy import deepcopy
from .identity import decode
from .organization_snapshot import snapshot
from .empirical_transport_check import verify_empirical_transport
from .acquisition_witness import certify_acquisition_witness
from .compact_measured_path import _decimal_count
from .role_work import RoleSearchBudget


def _inputs(model, transport, acquisition, events, measurements):
    if not verify_empirical_transport(model, transport):
        raise ValueError('Invalid empirical transport')
    view = snapshot(acquisition)
    witness = certify_acquisition_witness(view, measurements)
    if not isinstance(events, list) or not events:
        raise ValueError('Nonempty operator occurrences required')
    covered = set(); observations = []; records = []
    index = {(r['source'], r['frame']): r for r in measurements}
    if len(index) != len(measurements): raise ValueError('One measurement per frame required')
    for event, layout in enumerate(events):
        if not isinstance(layout, dict) or set(layout) != {'source','start','action','stop'}:
            raise ValueError('Invalid operator layout')
        source = layout['source']
        if source not in view.episodes or any(type(layout[k]) is not int for k in ('start','action','stop')):
            raise ValueError('Invalid operator source or bounds')
        frames = view.episodes[source][0]; start, action, stop = (layout[k] for k in ('start','action','stop'))
        if not 0 <= start < action < stop-1 < len(frames): raise ValueError('Before/action/after required')
        before = [decode(f) for f in frames[start:action]]; after = [decode(f) for f in frames[action+1:stop]]
        raw_action = decode(frames[action]); batch = []
        for frame in range(start, stop):
            key = (source, frame)
            if key in covered or key not in index: raise ValueError('Missing or duplicate occurrence')
            covered.add(key); row = index[key]
            if row['start'] != 0 or row['stop'] != len(frames[frame]): raise ValueError('Whole-frame measurement required')
            batch.append(dict(row))
        records.append(batch)
        origin = transport['domain'].index(before) if before in transport['domain'] else None
        destination = transport['domain'].index(after) if after in transport['domain'] else None
        status = 'UNKNOWN'
        if origin is not None and raw_action in transport['actions']:
            row = next(r for r in transport['rows'] if r['from_context'] == origin and r['action'] == raw_action)
            if any(out['frames'] == after for out in row['outputs']): status = 'SUPPORTED'
            elif not row['open']: status = 'UNSUPPORTED'
        observations.append(dict(event=event,before=before,action=raw_action,after=after,
                                 from_context=origin,to_context=destination,status=status))
    expected = {(s, i) for s,(frames,_) in view.episodes.items() for i in range(len(frames))}
    if covered != expected or set(index) != expected: raise ValueError('Complete acquisition coverage required')
    return witness, observations, records


def certify_operator_windows(model, transport, acquisition, events, measurements, *, max_search_steps=None):
    budget = RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume(); model = snapshot(model); acquisition = snapshot(acquisition)
        transport, events, measurements = deepcopy(transport), deepcopy(events), deepcopy(measurements)
        witness, observations, records = _inputs(model,transport,acquisition,events,measurements)
        base = dict(policy='measured_operator_windows_v1',transport=transport,events=events,
                    witness=witness,observations=observations)
        if len({r['clock'] for batch in records for r in batch}) != 1:
            return dict(**base,status='CLOCK_UNDETERMINED',nodes=[],edges=[],terminals=[],action_orders=[],total=None)
        n = len(events); sizes = tuple(map(len,records)); root = ((0,)*n,None,())
        states = [root]; lookup = {root:0}; counts = [1]; edges = []; cursor = 0
        while cursor < len(states):
            budget.consume(); progress, time, actions = states[cursor]
            for event in range(n):
                budget.consume(); position = progress[event]
                if position == sizes[event]: continue
                r = records[event][position]; earliest = r['lower'] if time is None else max(time,r['lower'])
                if earliest > r['upper']: continue
                next_progress = list(progress); next_progress[event] += 1
                trace = actions+(event,) if position+events[event]['start'] == events[event]['action'] else actions
                key = (tuple(next_progress),earliest,trace)
                if key not in lookup: lookup[key] = len(states); states.append(key); counts.append(0)
                target = lookup[key]; counts[target] += counts[cursor]
                edges.append([cursor,target,event,position+events[event]['start']])
            cursor += 1
        terminals = [i for i,s in enumerate(states) if s[0] == sizes]; bins = {}
        for i in terminals:
            budget.consume(); entry = bins.setdefault(states[i][2],[0,[]]); entry[0] += counts[i]; entry[1].append(i)
        orders = [dict(order=list(k),count=_decimal_count(v[0]),terminals=v[1]) for k,v in sorted(bins.items())]
        return dict(**base,status='TIME_COMPATIBLE_OPERATOR_WINDOWS' if terminals else 'TIME_CONTRADICTION',
                    nodes=[dict(progress=list(p),time=t,actions=list(a),count=_decimal_count(counts[i])) for i,(p,t,a) in enumerate(states)],
                    edges=edges,terminals=terminals,action_orders=orders,total=_decimal_count(sum(counts[i] for i in terminals)))

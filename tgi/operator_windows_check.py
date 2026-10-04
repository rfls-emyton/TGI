"""Independent exhaustive closure/count check for measured operator windows."""
from copy import deepcopy
from .identity import decode
from .organization_snapshot import snapshot
from .empirical_transport_check import verify_empirical_transport
from .acquisition_witness import verify_acquisition_witness
from .compact_measured_path import _decimal_count
from .frame_engine import canonical
from .role_work import RoleSearchBudget


def verify_operator_windows(model,transport,acquisition,events,measurements,certificate,*,max_search_steps=None):
    budget = RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            fields = {'policy','transport','events','witness','observations','status','nodes','edges','terminals','action_orders','total'}
            if set(certificate) != fields or certificate['policy'] != 'measured_operator_windows_v1': return False
            c = certificate; model = snapshot(model); view = snapshot(acquisition)
            events, measurements, transport = deepcopy(events),deepcopy(measurements),deepcopy(transport)
            if canonical(c['transport']) != canonical(transport) or canonical(c['events']) != canonical(events): return False
            if not verify_empirical_transport(model,transport) or not verify_acquisition_witness(view,measurements,c['witness']): return False
            if not isinstance(events,list) or not events: return False
            all_frames = {(s,i) for s,(frames,_) in view.episodes.items() for i in range(len(frames))}
            measured = {}
            for row in measurements:
                key = (row['source'],row['frame'])
                if key in measured or row['start'] != 0 or row['stop'] != len(view.episodes[row['source']][0][row['frame']]): return False
                measured[key] = row
            if set(measured) != all_frames: return False
            used = set(); observations = []; sequences = []
            for event, spec in enumerate(events):
                if not isinstance(spec,dict) or set(spec) != {'source','start','action','stop'}: return False
                if any(type(spec[k]) is not int for k in ('start','action','stop')) or spec['source'] not in view.episodes: return False
                frames = view.episodes[spec['source']][0]; first, action, end = spec['start'],spec['action'],spec['stop']
                if first < 0 or first >= action or action >= end-1 or end > len(frames): return False
                sequence = []
                for frame in range(first,end):
                    key = (spec['source'],frame)
                    if key in used: return False
                    used.add(key); sequence.append(measured[key])
                sequences.append(sequence)
                before = [decode(frames[i]) for i in range(first,action)]
                after = [decode(frames[i]) for i in range(action+1,end)]
                action_text = decode(frames[action]); origin = destination = None
                for i,context in enumerate(transport['domain']):
                    if context == before: origin = i
                    if context == after: destination = i
                classification = 'UNKNOWN'
                if origin is not None and action_text in transport['actions']:
                    rows = [r for r in transport['rows'] if r['from_context'] == origin and r['action'] == action_text]
                    if len(rows) != 1: return False
                    row = rows[0]
                    if after in [entry['frames'] for entry in row['outputs']]: classification = 'SUPPORTED'
                    elif row['open'] is False: classification = 'UNSUPPORTED'
                observations.append(dict(event=event,before=before,action=action_text,after=after,
                                         from_context=origin,to_context=destination,status=classification))
            if used != all_frames or canonical(observations) != canonical(c['observations']): return False
            clocks = {r['clock'] for r in measured.values()}
            if len(clocks) != 1:
                return c['status'] == 'CLOCK_UNDETERMINED' and c['nodes'] == [] and c['edges'] == [] and c['terminals'] == [] and c['action_orders'] == [] and c['total'] is None
            n = len(events); sizes = tuple(len(s) for s in sequences); states = []; lookup = {}
            for index,node in enumerate(c['nodes']):
                budget.consume()
                if set(node) != {'progress','time','actions','count'}: return False
                p,t,a = node['progress'],node['time'],node['actions']
                if not isinstance(p,list) or len(p) != n or any(type(x) is not int or not 0 <= x <= sizes[i] for i,x in enumerate(p)): return False
                if not isinstance(a,list) or any(type(e) is not int or not 0 <= e < n for e in a) or len(set(a)) != len(a): return False
                consumed = {e for e in range(n) if p[e] > events[e]['action']-events[e]['start']}
                if set(a) != consumed: return False
                if index == 0:
                    if p != [0]*n or t is not None or a != []: return False
                elif type(t) is not int or sum(p) == 0: return False
                key = (tuple(p),t,tuple(a))
                if key in lookup: return False
                lookup[key] = index; states.append(key)
            if not states: return False
            incoming = [[] for _ in states]; edges = []
            for index,(progress,time,trace) in enumerate(states):
                budget.consume()
                for event in range(n):
                    budget.consume(); offset = progress[event]
                    if offset >= sizes[event]: continue
                    row = sequences[event][offset]
                    candidate_time = row['lower']
                    if time is not None and time > candidate_time: candidate_time = time
                    if candidate_time > row['upper']: continue
                    updated = tuple(value+int(i==event) for i,value in enumerate(progress))
                    action_trace = tuple(list(trace)+[event]) if offset == events[event]['action']-events[event]['start'] else trace
                    key = (updated,candidate_time,action_trace)
                    if key not in lookup: return False
                    target = lookup[key]; incoming[target].append(index)
                    edges.append([index,target,event,events[event]['start']+offset])
            if canonical(edges) != canonical(c['edges']): return False
            counts = [0]*len(states); counts[0] = 1
            for i in sorted(range(1,len(states)),key=lambda j:sum(states[j][0])):
                budget.consume(); counts[i] = sum(counts[j] for j in incoming[i])
            if any(value <= 0 for value in counts): return False
            if any(node['count'] != _decimal_count(counts[i]) for i,node in enumerate(c['nodes'])): return False
            terminals = [i for i,s in enumerate(states) if s[0] == sizes]
            if canonical(terminals) != canonical(c['terminals']): return False
            groups = {}
            for index in terminals:
                budget.consume(); key = states[index][2]
                if key not in groups: groups[key] = [0,[]]
                groups[key][0] += counts[index]; groups[key][1].append(index)
            expected_orders = [dict(order=list(k),count=_decimal_count(v[0]),terminals=v[1]) for k,v in sorted(groups.items())]
            status = 'TIME_COMPATIBLE_OPERATOR_WINDOWS' if terminals else 'TIME_CONTRADICTION'
            return c['status'] == status and canonical(c['action_orders']) == canonical(expected_orders) and c['total'] == _decimal_count(sum(counts[i] for i in terminals))
        except (ValueError,TypeError,KeyError,IndexError,AttributeError,StopIteration):
            return False

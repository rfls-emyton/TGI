"""Native separating chains over complete ordered geometric outcome traces."""
from copy import deepcopy
from itertools import product
from .identity import encode,decode
from .organization_snapshot import snapshot
from .intervention_roles import certify_intervention_roles
from .intervention_composition import certify_intervention_compositions
from .acquisition_witness import certify_acquisition_witness
from .incidence import _endpoint
from .role_work import RoleSearchBudget


def certify_intervention_sequence_experiments(model,groups,measurements,seed,max_depth,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        if not isinstance(seed,str) or not seed or type(max_depth) is not int or max_depth<1:raise ValueError('Raw seed and positive integer depth required')
        encode(seed);view=snapshot(model);roles=certify_intervention_roles(view,deepcopy(groups),deepcopy(measurements));classes=sorted({tuple(b) for p in roles['partitions'] for b in p['blocks']});actions=sorted({decode(f[1]) for f,_ in view.episodes.values()});sequences=[]
        for length in range(1,max_depth+1):
            for sequence in product(actions,repeat=length):budget.consume();sequences.append(sequence)
        cached={}
        for port in sorted({i for b in classes for i in b}):
            budget.consume();cached[port]=certify_intervention_compositions(view,groups,measurements,roles['ports'][port],seed,[list(s) for s in sequences])
        rows=[];n=len(classes)
        for index,sequence in enumerate(sequences):
            predictions=[];outcomes={};complete=True
            for i,block in enumerate(classes):
                budget.consume();certificates=[];traces=set();complete &= any(c['ports']==list(block) and c['eligible'] for c in roles['role_candidates'])
                for port in block:
                    budget.consume();c=cached[port][index];certificates.append(c);ready=c['result']['status']=='COMPOSED_ROLE_RESOLUTION';complete &= ready
                    if ready:traces.add(tuple(s['result']['output'][0] for s in c['steps']))
                predictions.append({'class':i,'compositions':certificates,'traces':[list(t) for t in sorted(traces)]})
                for trace in traces:outcomes.setdefault(trace,[]).append(i)
            worst=max((len(ids) for ids in outcomes.values()),default=n) if complete else n
            rows.append({'actions':list(sequence),'predictions':predictions,'outcomes':[{'trace':list(t),'classes':ids} for t,ids in sorted(outcomes.items())],'complete':bool(complete),'worst_remaining':worst})
        eligible=[r for r in rows if r['complete'] and r['worst_remaining']<n];length=min((len(r['actions']) for r in eligible),default=None);best=min((r['worst_remaining'] for r in eligible if len(r['actions'])==length),default=n);chosen=[r['actions'] for r in eligible if len(r['actions'])==length and r['worst_remaining']==best]
        status='SEQUENCE_EXPERIMENT_READY' if chosen else 'NO_SEPARATOR_WITHIN_DEPTH' if all(r['complete'] for r in rows) else 'INCOMPLETE_GEOMETRY'
        return {'policy':'native_sequence_experiment_v1','seed':seed,'max_depth':max_depth,'roles':roles,'classes':[list(b) for b in classes],'rows':rows,'result':{'status':status,'sequences':chosen,'shortest_admitted_length':length,'worst_remaining':best,'initial_classes':n}}


def certify_sequence_observation(model,groups,measurements,seed,max_depth,plan,acquisition,acquired_groups,observed_measurements,sources,*,max_search_steps=None):
    from .intervention_sequence_experiment_check import verify_intervention_sequence_experiments
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        if not verify_intervention_sequence_experiments(model,groups,measurements,seed,max_depth,plan):raise ValueError('Invalid or stale plan')
        if not isinstance(sources,(list,tuple)) or not sources or any(not isinstance(s,str) or not s for s in sources) or len(set(sources))!=len(sources):raise ValueError('Ordered unique original sources required')
        view=snapshot(acquisition);witness=certify_acquisition_witness(view,observed_measurements);lookup={(r['source'],r['frame']):r for r in observed_measurements};expected={(s,i) for s,(f,_) in view.episodes.items() for i in range(len(f))}
        if len(lookup)!=len(observed_measurements) or set(lookup)!=expected or any(r['start']!=0 or r['stop']!=len(view.episodes[s][0][i]) for (s,i),r in lookup.items()):raise ValueError('Complete whole-frame coverage required')
        if not isinstance(acquired_groups,list) or not acquired_groups or any(not isinstance(g,list) or not g for g in acquired_groups):raise ValueError('Nonempty raw view groups required')
        assignment={}
        for group in acquired_groups:
            ports=set()
            for spec in group:
                if not isinstance(spec,dict) or set(spec)!={'port','source'} or spec['port'] in ports or spec['source'] in assignment:raise ValueError('Complete unique original view layout required')
                encode(spec['port']);ports.add(spec['port']);assignment[spec['source']]=spec['port']
        if set(assignment)!=set(view.episodes) or any(s not in assignment for s in sources) or any(len(f)!=3 for f,_ in view.episodes.values()):raise ValueError('Complete three-frame source layout required')
        actions=[];trace=[];points=[];current=seed;clock=None;previous_upper=None;ordered=len({assignment[s] for s in sources})==1
        for source in sources:
            budget.consume();frames=view.episodes[source][0];before,action,after=map(decode,frames);b,a,z=(lookup[source,i] for i in range(3));clock=b['clock'] if clock is None else clock
            ordered &= before==current and b['clock']==a['clock']==z['clock']==clock and b['upper']<=a['lower'] and a['upper']<=z['lower'] and (previous_upper is None or previous_upper<b['lower'])
            for other,(raw,_) in view.episodes.items():
                budget.consume();r=lookup[other,1];shared=(r['clock'],r['lower'],r['upper'])==(a['clock'],a['lower'],a['upper']) and decode(raw[1])==action
                ordered &= shared or (r['clock']==clock and (r['upper']<b['lower'] or r['lower']>z['upper']))
            actions.append(action);trace.append(after);points.append({'source':source,'occurrences':[_endpoint(view,source,(i,0,len(f))) for i,f in enumerate(frames)]});current=after;previous_upper=z['upper']
        candidates=list(range(len(plan['classes'])));status='INCOMPLETE_OBSERVATION'
        if ordered:
            if actions not in plan['result']['sequences']:status='UNPLANNED_SEQUENCE'
            else:
                row=next(r for r in plan['rows'] if r['actions']==actions);candidates=next((r['classes'] for r in row['outcomes'] if r['trace']==trace),[]);status='CLASS_PROFILE_IDENTIFIED' if len(candidates)==1 else 'CLASS_PROFILE_AMBIGUOUS' if candidates else 'UNMODELED_RESPONSE'
        return {'policy':'native_sequence_observation_v1','plan':deepcopy(plan),'sources':list(sources),'groups':deepcopy(acquired_groups),'witness':witness,'points':points,'result':{'status':status,'ordered':bool(ordered),'trace':trace,'candidate_classes':list(candidates),'candidate_blocks':[plan['classes'][i] for i in candidates]}}

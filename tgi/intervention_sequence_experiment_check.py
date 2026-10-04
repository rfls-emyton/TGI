"""Independent exhaustive sequence, geometric trace and measured acquisition checks."""
from copy import deepcopy
from itertools import product
from .identity import encode,decode
from .frame_engine import canonical
from .organization_snapshot import snapshot
from .intervention_roles_check import verify_intervention_roles
from .intervention_composition_check import verify_intervention_compositions
from .acquisition_witness import verify_acquisition_witness
from .role_work import RoleSearchBudget


def verify_intervention_sequence_experiments(model,groups,measurements,seed,max_depth,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        if isinstance(certificate,dict) and certificate.get('policy')=='native_scoped_sequence_experiment_v1':
            from .scoped_sequence_experiment_check import verify_scoped_sequence_experiments
            return verify_scoped_sequence_experiments(model,groups,measurements,seed,max_depth,certificate)
        try:
            if not isinstance(seed,str) or not seed or type(max_depth) is not int or max_depth<1:return False
            encode(seed);c=deepcopy(certificate)
            if set(c)!={'policy','seed','max_depth','roles','classes','rows','result'} or c['policy']!='native_sequence_experiment_v1' or c['seed']!=seed or type(c['max_depth']) is not int or c['max_depth']!=max_depth:return False
            view=snapshot(model);roles=c['roles']
            if not verify_intervention_roles(view,groups,measurements,roles):return False
            blocks=sorted({tuple(b) for p in roles['partitions'] for b in p['blocks']});classes=[list(b) for b in blocks];actions=sorted({decode(f[1]) for f,_ in view.episodes.values()});sequences=[]
            for length in range(1,max_depth+1):
                for sequence in product(actions,repeat=length):budget.consume();sequences.append(list(sequence))
            if canonical(c['classes'])!=canonical(classes) or not isinstance(c['rows'],list) or len(c['rows'])!=len(sequences):return False
            checked={}
            for port in sorted({i for block in blocks for i in block}):
                budget.consume();ci=next(i for i,b in enumerate(blocks) if port in b);position=blocks[ci].index(port);children=[row['predictions'][ci]['compositions'][position] for row in c['rows']]
                if not verify_intervention_compositions(view,groups,measurements,roles['ports'][port],seed,sequences,children):return False
                checked[port]=children
            n=len(blocks);summaries=[]
            for row_index,(sequence,row) in enumerate(zip(sequences,c['rows'])):
                budget.consume()
                if set(row)!={'actions','predictions','outcomes','complete','worst_remaining'} or row['actions']!=sequence or len(row['predictions'])!=n:return False
                response={};complete=True
                for i,(block,prediction) in enumerate(zip(blocks,row['predictions'])):
                    if set(prediction)!={'class','compositions','traces'} or type(prediction['class']) is not int or prediction['class']!=i or len(prediction['compositions'])!=len(block):return False
                    traces=set();complete &= any(x['ports']==list(block) and x['eligible'] for x in roles['role_candidates'])
                    for port,child in zip(block,prediction['compositions']):
                        budget.consume()
                        if canonical(child)!=canonical(checked[port][row_index]):return False
                        ready=child['result']['status']=='COMPOSED_ROLE_RESOLUTION';complete &= ready
                        if ready:traces.add(tuple(s['result']['output'][0] for s in child['steps']))
                    if canonical(prediction['traces'])!=canonical([list(t) for t in sorted(traces)]):return False
                    for trace in traces:response.setdefault(trace,[]).append(i)
                outcomes=[{'trace':list(t),'classes':ids} for t,ids in sorted(response.items())];worst=max((len(ids) for ids in response.values()),default=n) if complete else n
                if canonical(row['outcomes'])!=canonical(outcomes) or canonical(row['complete'])!=canonical(bool(complete)) or type(row['worst_remaining']) is not int or row['worst_remaining']!=worst:return False
                summaries.append((sequence,bool(complete),worst))
            admitted=[(s,w) for s,ok,w in summaries if ok and w<n];length=min((len(s) for s,w in admitted),default=None);best=min((w for s,w in admitted if len(s)==length),default=n);chosen=[s for s,w in admitted if len(s)==length and w==best];status='SEQUENCE_EXPERIMENT_READY' if chosen else 'NO_SEPARATOR_WITHIN_DEPTH' if all(ok for _,ok,_ in summaries) else 'INCOMPLETE_GEOMETRY'
            return canonical(c['result'])==canonical({'status':status,'sequences':chosen,'shortest_admitted_length':length,'worst_remaining':best,'initial_classes':n})
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False


def verify_sequence_observation(model,groups,measurements,seed,max_depth,plan,acquisition,acquired_groups,observed_measurements,sources,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            c=deepcopy(certificate)
            if set(c)!={'policy','plan','sources','groups','witness','points','result'} or c['policy']!='native_sequence_observation_v1' or canonical(c['plan'])!=canonical(plan) or canonical(c['sources'])!=canonical(list(sources)) or canonical(c['groups'])!=canonical(acquired_groups):return False
            if not verify_intervention_sequence_experiments(model,groups,measurements,seed,max_depth,plan):return False
            if not isinstance(sources,(list,tuple)) or not sources or any(not isinstance(s,str) or not s for s in sources) or len(set(sources))!=len(sources):return False
            view=snapshot(acquisition)
            if not verify_acquisition_witness(view,observed_measurements,c['witness']):return False
            lookup={(r['source'],r['frame']):r for r in observed_measurements};expected={(s,i) for s,(f,_) in view.episodes.items() for i in range(len(f))}
            if len(lookup)!=len(observed_measurements) or set(lookup)!=expected or any(r['start']!=0 or r['stop']!=len(view.episodes[s][0][i]) for (s,i),r in lookup.items()):return False
            if not isinstance(acquired_groups,list) or not acquired_groups or any(not isinstance(g,list) or not g for g in acquired_groups):return False
            assignment={}
            for group in acquired_groups:
                ports=set()
                for spec in group:
                    if not isinstance(spec,dict) or set(spec)!={'port','source'} or spec['port'] in ports or spec['source'] in assignment:return False
                    encode(spec['port']);ports.add(spec['port']);assignment[spec['source']]=spec['port']
            if set(assignment)!=set(view.episodes) or any(s not in assignment for s in sources) or any(len(f)!=3 for f,_ in view.episodes.values()):return False
            port=assignment[sources[0]];ordered=all(assignment[s]==port for s in sources);actions=[];trace=[];points=[];current=seed;clock=None;end=None
            for source in sources:
                budget.consume();frames,receipts=view.episodes[source];before,action,after=map(decode,frames);b,a,z=(lookup[source,i] for i in range(3));clock=b['clock'] if clock is None else clock
                if before!=current or b['clock']!=clock or a['clock']!=clock or z['clock']!=clock or b['upper']>a['lower'] or a['upper']>z['lower'] or (end is not None and end>=b['lower']):ordered=False
                for other,(raw,_) in view.episodes.items():
                    budget.consume();r=lookup[other,1];shared=r['clock']==a['clock'] and r['lower']==a['lower'] and r['upper']==a['upper'] and decode(raw[1])==action
                    if not shared and (r['clock']!=clock or not (r['upper']<b['lower'] or r['lower']>z['upper'])):ordered=False
                occurrences=[];offset=0
                for i,frame in enumerate(frames):
                    origin=receipts[i].origin;n=len(frame);occurrences.append({'frame':i,'start':0,'stop':n,'event_span':[offset,offset+n],'identities':list(frame),'coordinates':[[origin[0]+j,*origin[1:]] for j in range(n)]});offset+=n
                points.append({'source':source,'occurrences':occurrences});actions.append(action);trace.append(after);current=after;end=z['upper']
            candidates=list(range(len(plan['classes'])));status='INCOMPLETE_OBSERVATION'
            if ordered:
                if actions not in plan['result']['sequences']:status='UNPLANNED_SEQUENCE'
                else:
                    row=next(r for r in plan['rows'] if r['actions']==actions);candidates=next((r['classes'] for r in row['outcomes'] if r['trace']==trace),[]);status='CLASS_PROFILE_IDENTIFIED' if len(candidates)==1 else 'CLASS_PROFILE_AMBIGUOUS' if candidates else 'UNMODELED_RESPONSE'
            result={'status':status,'ordered':bool(ordered),'trace':trace,'candidate_classes':list(candidates),'candidate_blocks':[plan['classes'][i] for i in candidates]}
            return canonical(c['points'])==canonical(points) and canonical(c['result'])==canonical(result)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

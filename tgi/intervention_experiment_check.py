"""Independent complete intervention experiment and acquisition refinement checks."""
from copy import deepcopy
from .identity import encode,decode
from .frame_engine import canonical
from .organization_snapshot import snapshot
from .intervention_roles_check import verify_intervention_roles
from .intervention_composition_check import verify_intervention_composition
from .acquisition_witness import verify_acquisition_witness
from .role_work import RoleSearchBudget


def verify_intervention_experiments(model,groups,measurements,seed,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            if not isinstance(seed,str) or not seed:return False
            encode(seed);c=deepcopy(certificate)
            if set(c)!={'policy','seed','roles','classes','rows','result'} or c['policy']!='native_intervention_experiment_v1' or c['seed']!=seed:return False
            view=snapshot(model);roles=c['roles']
            if not verify_intervention_roles(view,groups,measurements,roles):return False
            blocks=sorted({tuple(b) for p in roles['partitions'] for b in p['blocks']});classes=[list(b) for b in blocks];actions=sorted({decode(f[1]) for f,_ in view.episodes.values()});n=len(blocks)
            if canonical(c['classes'])!=canonical(classes) or not isinstance(c['rows'],list) or len(c['rows'])!=len(actions):return False
            rows=[]
            for action,row in zip(actions,c['rows']):
                budget.consume()
                if set(row)!={'action','predictions','outcomes','complete','worst_remaining'} or row['action']!=action or len(row['predictions'])!=n:return False
                response={};complete=True
                for i,(block,prediction) in enumerate(zip(blocks,row['predictions'])):
                    if set(prediction)!={'class','compositions','outputs'} or type(prediction['class']) is not int or prediction['class']!=i or len(prediction['compositions'])!=len(block):return False
                    outputs=set();complete &= any(x['ports']==list(block) and x['eligible'] for x in roles['role_candidates'])
                    for port,child in zip(block,prediction['compositions']):
                        budget.consume()
                        if not verify_intervention_composition(view,groups,measurements,roles['ports'][port],seed,[action],child):return False
                        ready=child['result']['status']=='COMPOSED_ROLE_RESOLUTION';complete &= ready
                        if ready:outputs.update(child['result']['output'])
                    if canonical(prediction['outputs'])!=canonical(sorted(outputs)):return False
                    for value in outputs:response.setdefault(value,[]).append(i)
                expected=[{'after':v,'classes':ids} for v,ids in sorted(response.items())];worst=max((len(ids) for ids in response.values()),default=n) if complete else n
                if canonical(row['outcomes'])!=canonical(expected) or canonical(row['complete'])!=canonical(bool(complete)) or type(row['worst_remaining']) is not int or row['worst_remaining']!=worst:return False
                rows.append((action,bool(complete),worst))
            best=min((w for _,ok,w in rows if ok),default=n);chosen=[a for a,ok,w in rows if ok and w==best and best<n];status='EXPERIMENT_READY' if chosen else 'NO_SEPARATOR' if all(ok for _,ok,_ in rows) else 'INCOMPLETE_GEOMETRY'
            result={'status':status,'actions':chosen,'worst_remaining':best,'initial_classes':n}
            return canonical(c['result'])==canonical(result)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False


def verify_experiment_observation(model,groups,measurements,seed,plan,acquisition,observed_measurements,source,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            c=deepcopy(certificate)
            if set(c)!={'policy','plan','source','witness','occurrences','result'} or c['policy']!='native_experiment_observation_v1' or c['source']!=source or canonical(c['plan'])!=canonical(plan):return False
            if not verify_intervention_experiments(model,groups,measurements,seed,plan):return False
            view=snapshot(acquisition)
            if not verify_acquisition_witness(view,observed_measurements,c['witness']):return False
            lookup={(r['source'],r['frame']):r for r in observed_measurements};expected={(s,i) for s,(frames,_) in view.episodes.items() for i in range(len(frames))}
            if len(lookup)!=len(observed_measurements) or set(lookup)!=expected or any(r['start']!=0 or r['stop']!=len(view.episodes[s][0][i]) for (s,i),r in lookup.items()):return False
            frames,receipts=view.episodes[source]
            if len(frames)!=3:return False
            before,action,after=map(decode,frames);b,a,z=(lookup[source,i] for i in range(3));ordered=b['clock']==a['clock']==z['clock'] and b['upper']<=a['lower'] and a['upper']<=z['lower']
            for s,(f,_) in view.episodes.items():
                budget.consume()
                if len(f)!=3:return False
                r=lookup[s,1];shared=r['clock']==a['clock'] and r['lower']==a['lower'] and r['upper']==a['upper'] and decode(f[1])==action
                if not shared and (r['clock']!=b['clock'] or not (r['upper']<b['lower'] or r['lower']>z['upper'])):ordered=False
            points=[];offset=0
            for i,frame in enumerate(frames):
                origin=receipts[i].origin;n=len(frame);points.append({'frame':i,'start':0,'stop':n,'event_span':[offset,offset+n],'identities':list(frame),'coordinates':[[origin[0]+j,*origin[1:]] for j in range(n)]});offset+=n
            candidates=list(range(len(plan['classes'])));status='INCOMPLETE_OBSERVATION'
            if ordered and before==seed:
                if action not in plan['result']['actions']:status='UNPLANNED_ACTION'
                else:
                    row=next(r for r in plan['rows'] if r['action']==action);candidates=next((r['classes'] for r in row['outcomes'] if r['after']==after),[]);status='CLASS_PROFILE_IDENTIFIED' if len(candidates)==1 else 'CLASS_PROFILE_AMBIGUOUS' if candidates else 'UNMODELED_RESPONSE'
            result={'status':status,'ordered':bool(ordered),'candidate_classes':list(candidates),'candidate_blocks':[plan['classes'][i] for i in candidates]}
            return canonical(c['occurrences'])==canonical(points) and canonical(c['result'])==canonical(result)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

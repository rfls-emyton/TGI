"""Native experiments chosen by complete geometric outcome separation."""
from copy import deepcopy
from .identity import encode,decode
from .organization_snapshot import snapshot
from .intervention_roles import certify_intervention_roles
from .intervention_composition import certify_intervention_compositions
from .acquisition_witness import certify_acquisition_witness
from .incidence import _endpoint
from .role_work import RoleSearchBudget


def certify_intervention_experiments(model,groups,measurements,seed,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        if not isinstance(seed,str) or not seed:raise ValueError('Nonempty raw probe seed required')
        encode(seed);view=snapshot(model);roles=certify_intervention_roles(view,deepcopy(groups),deepcopy(measurements))
        classes=sorted({tuple(b) for partition in roles['partitions'] for b in partition['blocks']});actions=sorted({decode(frames[1]) for frames,_ in view.episodes.values()});rows=[];n=len(classes)
        cached={}
        for port in sorted({p for block in classes for p in block}):
            budget.consume();cached[port]=dict(zip(actions,certify_intervention_compositions(view,groups,measurements,roles['ports'][port],seed,[[a] for a in actions])))
        for action in actions:
            predictions=[];outcomes={};complete=True
            for i,block in enumerate(classes):
                budget.consume();certificates=[];outputs=set()
                complete &= any(r['ports']==list(block) and r['eligible'] for r in roles['role_candidates'])
                for port in block:
                    budget.consume();c=cached[port][action];certificates.append(c)
                    ready=c['result']['status']=='COMPOSED_ROLE_RESOLUTION';complete &= ready
                    if ready:outputs.update(c['result']['output'])
                predictions.append({'class':i,'compositions':certificates,'outputs':sorted(outputs)})
                for output in outputs:outcomes.setdefault(output,[]).append(i)
            response=[{'after':value,'classes':ids} for value,ids in sorted(outcomes.items())];worst=max((len(ids) for ids in outcomes.values()),default=n) if complete else n
            rows.append({'action':action,'predictions':predictions,'outcomes':response,'complete':bool(complete),'worst_remaining':worst})
        best=min((r['worst_remaining'] for r in rows if r['complete']),default=n);chosen=[r['action'] for r in rows if r['complete'] and r['worst_remaining']==best and best<n]
        status='EXPERIMENT_READY' if chosen else 'NO_SEPARATOR' if all(r['complete'] for r in rows) else 'INCOMPLETE_GEOMETRY'
        return {'policy':'native_intervention_experiment_v1','seed':seed,'roles':roles,'classes':[list(b) for b in classes],'rows':rows,'result':{'status':status,'actions':chosen,'worst_remaining':best,'initial_classes':n}}


def certify_experiment_observation(model,groups,measurements,seed,plan,acquisition,observed_measurements,source,*,max_search_steps=None):
    from .intervention_experiment_check import verify_intervention_experiments
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        if not verify_intervention_experiments(model,groups,measurements,seed,plan):raise ValueError('Invalid or stale plan')
        view=snapshot(acquisition);witness=certify_acquisition_witness(view,observed_measurements)
        if source not in view.episodes or len(view.episodes[source][0])!=3:raise ValueError('Original before/action/after source required')
        lookup={(r['source'],r['frame']):r for r in observed_measurements};expected={(s,i) for s,(frames,_) in view.episodes.items() for i in range(len(frames))}
        if len(lookup)!=len(observed_measurements) or set(lookup)!=expected or any(r['start']!=0 or r['stop']!=len(view.episodes[s][0][i]) for (s,i),r in lookup.items()):raise ValueError('Complete whole-frame measurement coverage required')
        frames=view.episodes[source][0];before,action,after=map(decode,frames);b,a,z=(lookup[source,i] for i in range(3));ordered=len({b['clock'],a['clock'],z['clock']})==1 and b['upper']<=a['lower'] and a['upper']<=z['lower']
        for s,(other,_) in view.episodes.items():
            budget.consume()
            if len(other)!=3:raise ValueError('Exactly three frames per acquired view')
            r=lookup[s,1];same=(r['clock'],r['lower'],r['upper'])==(a['clock'],a['lower'],a['upper']) and decode(other[1])==action
            ordered &= same or (r['clock']==b['clock'] and (r['upper']<b['lower'] or r['lower']>z['upper']))
        candidates=list(range(len(plan['classes'])));status='INCOMPLETE_OBSERVATION'
        if ordered and before==seed:
            if action not in plan['result']['actions']:status='UNPLANNED_ACTION'
            else:
                row=next(r for r in plan['rows'] if r['action']==action);candidates=next((r['classes'] for r in row['outcomes'] if r['after']==after),[])
                status='CLASS_PROFILE_IDENTIFIED' if len(candidates)==1 else 'CLASS_PROFILE_AMBIGUOUS' if candidates else 'UNMODELED_RESPONSE'
        return {'policy':'native_experiment_observation_v1','plan':deepcopy(plan),'source':source,'witness':witness,'occurrences':[_endpoint(view,source,(i,0,len(frame))) for i,frame in enumerate(frames)],'result':{'status':status,'ordered':bool(ordered),'candidate_classes':list(candidates),'candidate_blocks':[plan['classes'][i] for i in candidates]}}

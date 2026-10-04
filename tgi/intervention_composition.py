"""Composition of native channel transformations, with original character lineage."""
from copy import deepcopy
from .identity import encode
from .organization_snapshot import snapshot
from .intervention_resolution import certify_intervention_resolution
from .intervention_scope import decode_scope
from .role_work import RoleSearchBudget

_SHARED=('roles','root_port','source_scope','inventory','role_alternatives')


def certify_intervention_composition(acquisition,groups,measurements,root_port,seed,actions,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        if not isinstance(seed,str) or not seed:raise ValueError('Nonempty raw seed required')
        encode(seed)
        if not isinstance(actions,(list,tuple)) or not actions or any(not isinstance(a,str) or not a for a in actions):raise ValueError('Ordered nonempty raw actions required')
        actions=list(actions)
        for a in actions:encode(a)
        view=snapshot(acquisition);groups,measurements=deepcopy(groups),deepcopy(measurements)
        first=certify_intervention_resolution(view,groups,measurements,root_port,seed,actions[0])
        shared={k:first[k] for k in _SHARED};local=decode_scope(view,shared['source_scope'],shared['inventory'])
        return _compose_scoped(local,shared,root_port,seed,actions,first['response'],budget)


def _compose_scoped(local,shared,root_port,seed,actions,first_response,budget):
    role_ready=bool(shared['role_alternatives']) and all(a['eligible'] for a in shared['role_alternatives'])
    current=seed;lineage=[{'kind':'seed','position':i} for i in range(len(encode(seed)))];steps=[];blocked=None;completed=0
    for index,action in enumerate(actions):
        budget.consume()
        response=first_response if index==0 and first_response is not None else local.resolve([current,action],terminal_only=True)
        ready=role_ready and response['status']=='RESOLVED'
        result={'status':'ROLE_STRUCTURAL_RESOLUTION' if ready else 'UNRESOLVED','output':response['output'] if ready else []};next_lineage=[]
        if ready:
            if len(response['output'])!=1:raise ValueError('Exactly one after frame required')
            trace=response['proofs'][0]['characters'][0]
            for point in trace:
                budget.consume()
                if point['kind']=='trigger':
                    next_lineage.append(dict(lineage[point['position']]) if point['frame']==0 else {'kind':'action','step':index,'position':point['position']})
                else:next_lineage.append(dict(point))
        steps.append({'before':current,'action':action,'response':response,'result':result,'lineage':next_lineage})
        if not ready:blocked=index;break
        completed+=1;current=response['output'][0];lineage=next_lineage
    return {'policy':'native_intervention_composition_v1','root_port':root_port,'seed':seed,'actions':actions,'substrate':shared,'steps':steps,
            'result':{'status':'COMPOSED_ROLE_RESOLUTION' if blocked is None else 'UNRESOLVED','output':[current] if blocked is None else [],'completed_steps':completed,'blocked_at':blocked,'lineage':lineage if blocked is None else []}}


def certify_intervention_compositions(acquisition,groups,measurements,root_port,seed,sequences,*,max_search_steps=None):
    """Independent query chains share one immutable native scoped formation."""
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        if not isinstance(sequences,(list,tuple)) or not sequences:raise ValueError('Nonempty query-chain batch required')
        for actions in sequences:
            if not isinstance(actions,(list,tuple)) or not actions or any(not isinstance(a,str) or not a for a in actions):raise ValueError('Ordered nonempty raw actions required')
            for action in actions:encode(action)
        view=snapshot(acquisition);groups,measurements=deepcopy(groups),deepcopy(measurements)
        first=certify_intervention_composition(view,groups,measurements,root_port,seed,sequences[0]);shared=first['substrate'];local=decode_scope(view,shared['source_scope'],shared['inventory']);results=[first]
        for actions in sequences[1:]:
            budget.consume();results.append(_compose_scoped(local,shared,root_port,seed,list(actions),None,budget))
        return results

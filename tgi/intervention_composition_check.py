"""Independent composition coverage, response and expanded lineage verifier."""
from copy import deepcopy
from .identity import encode
from .frame_engine import canonical
from .organization_snapshot import snapshot
from .intervention_scope import decode_scope
from .intervention_resolution_check import verify_intervention_resolution,verify_channel_response
from .role_work import RoleSearchBudget


def verify_intervention_composition(acquisition,groups,measurements,root_port,seed,actions,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            c=deepcopy(certificate)
            if set(c)!={'policy','root_port','seed','actions','substrate','steps','result'} or c['policy']!='native_intervention_composition_v1':return False
            if not isinstance(seed,str) or not seed or not isinstance(actions,(list,tuple)) or not actions or any(not isinstance(a,str) or not a for a in actions):return False
            encode(seed)
            for a in actions:encode(a)
            if c['root_port']!=root_port or c['seed']!=seed or canonical(c['actions'])!=canonical(list(actions)):return False
            shared=c['substrate']
            if set(shared)!={'roles','root_port','source_scope','inventory','role_alternatives'} or shared['root_port']!=root_port or not isinstance(c['steps'],list) or not c['steps']:return False
            first={**shared,'policy':'intervention_structural_resolution_v1','prefix':[seed,actions[0]],'response':c['steps'][0]['response'],'result':c['steps'][0]['result']}
            view=snapshot(acquisition)
            if not verify_intervention_resolution(view,groups,measurements,root_port,seed,actions[0],first):return False
            local=decode_scope(view,shared['source_scope'],shared['inventory'])
            return _verify_scoped_steps(local,shared,seed,actions,c,budget,False)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False


def _verify_scoped_steps(local,shared,seed,actions,c,budget,verify_first):
    role_ready=bool(shared['role_alternatives']) and all(a['eligible'] for a in shared['role_alternatives'])
    current=seed;owners=[{'kind':'seed','position':i} for i in range(len(encode(seed)))];completed=0;blocked=None
    for index,action in enumerate(actions):
        budget.consume()
        if index>=len(c['steps']):return False
        row=c['steps'][index]
        if set(row)!={'before','action','response','result','lineage'} or row['before']!=current or row['action']!=action:return False
        if (index or verify_first) and not verify_channel_response(local,current,action,row['response'],budget):return False
        response=row['response'];ready=role_ready and response['status']=='RESOLVED'
        result={'status':'ROLE_STRUCTURAL_RESOLUTION' if ready else 'UNRESOLVED','output':response['output'] if ready else []}
        if canonical(row['result'])!=canonical(result):return False
        expected=[]
        if ready:
            if len(response['output'])!=1:return False
            output_ids=encode(response['output'][0]);points=response['proofs'][0]['characters'][0]
            if len(points)!=len(output_ids):return False
            for identity,point in zip(output_ids,points):
                budget.consume()
                if point['kind']=='trigger':
                    position=point['position'];frame=point['frame']
                    if frame==0:expected.append(dict(owners[position]))
                    elif frame==1:expected.append({'kind':'action','step':index,'position':position})
                    else:return False
                elif point['kind']=='crystal':expected.append(dict(point))
                else:return False
        if canonical(row['lineage'])!=canonical(expected):return False
        if not ready:blocked=index;break
        current=response['output'][0];owners=expected;completed+=1
    if len(c['steps'])!=(len(actions) if blocked is None else blocked+1):return False
    expected_result={'status':'COMPOSED_ROLE_RESOLUTION' if blocked is None else 'UNRESOLVED','output':[current] if blocked is None else [],'completed_steps':completed,'blocked_at':blocked,'lineage':owners if blocked is None else []}
    return canonical(c['result'])==canonical(expected_result)


def verify_intervention_compositions(acquisition,groups,measurements,root_port,seed,sequences,certificates,*,max_search_steps=None):
    """Verify one complete immutable scope, then every query response and lineage."""
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            if not isinstance(sequences,(list,tuple)) or not sequences or not isinstance(certificates,list) or len(certificates)!=len(sequences):return False
            for actions in sequences:
                if not isinstance(actions,(list,tuple)) or not actions or any(not isinstance(a,str) or not a for a in actions):return False
                for action in actions:encode(action)
            copies=deepcopy(certificates);view=snapshot(acquisition)
            if not verify_intervention_composition(view,groups,measurements,root_port,seed,sequences[0],copies[0]):return False
            shared=copies[0]['substrate'];local=decode_scope(view,shared['source_scope'],shared['inventory'])
            for actions,c in zip(sequences[1:],copies[1:]):
                budget.consume()
                if set(c)!={'policy','root_port','seed','actions','substrate','steps','result'} or c['policy']!='native_intervention_composition_v1' or c['root_port']!=root_port or c['seed']!=seed or canonical(c['actions'])!=canonical(list(actions)) or canonical(c['substrate'])!=canonical(shared) or not isinstance(c['steps'],list) or not c['steps']:return False
                if not _verify_scoped_steps(local,shared,seed,actions,c,budget,True):return False
            return True
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

"""Complete role, scoped formation and character-lineage verification."""
from copy import deepcopy
from .identity import encode,decode
from .frame_engine import canonical
from .organization import RawOrganization,Organization,_match
from .phase_evidence import Opposition
from .organization_snapshot import snapshot
from .organization_inventory_check import verify_organization_inventory
from .organization_check import verify_resolution,verify_refusal
from .intervention_roles_check import verify_intervention_roles
from .role_work import RoleSearchBudget
from .intervention_scope import decode_scope


def verify_channel_response(local,before,action,response,budget):
    prefix=[before,action];raw=tuple(map(encode,prefix))
    if set(response)!={'status','output','candidates','proofs','revoked_candidates'}:return False
    outputs=set();unbound=False
    for h in local.organizations.values():
        budget.consume()
        if len(h.pattern)!=3:continue
        for bindings,_ in _match(h.pattern,raw):
            if not local._phase_valid(h):return False
            if len(bindings)!=len(h.diversity):unbound=True;continue
            outputs.add(tuple(decode(tuple(i for k,v in frame for i in (v if k=='lit' else bindings[v]))) for frame in h.pattern[2:]))
    revoked=[a for a,(h,_) in sorted(local.rejected_organizations.items()) if len(h.pattern)==3 and _match(h.pattern,raw)]
    status='AMBIGUOUS' if len(outputs)>1 or (outputs and unbound) else 'RESOLVED' if outputs else 'INCOMPLETE' if unbound else 'AMBIGUOUS' if revoked else 'NO_PATH'
    expected_output=list(next(iter(outputs))) if status=='RESOLVED' else []
    if response['status']!=status or response['output']!=expected_output or canonical(response['candidates'])!=canonical([list(o) for o in sorted(outputs)]) or response['revoked_candidates']!=revoked:return False
    if status=='RESOLVED':
        if not verify_resolution(local,prefix,response,terminal_only=True):return False
    elif status=='INCOMPLETE':
        if outputs or not unbound or response['proofs']!=[]:return False
    elif not verify_refusal(local,prefix,response,terminal_only=True):return False
    return True


def verify_intervention_resolution(acquisition,groups,measurements,root_port,before,action,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            c=deepcopy(certificate)
            if set(c)!={'policy','roles','root_port','prefix','source_scope','inventory','response','role_alternatives','result'} or c['policy']!='intervention_structural_resolution_v1':return False
            if not all(isinstance(x,str) and x for x in (root_port,before,action)):return False
            for x in (root_port,before,action):encode(x)
            if c['root_port']!=root_port or c['prefix']!=[before,action]:return False
            view=snapshot(acquisition)
            if not verify_intervention_roles(view,groups,measurements,c['roles']):return False
            ports=c['roles']['ports']
            if root_port not in ports:return False
            root=ports.index(root_port);scope=sorted(spec['source'] for group in groups for spec in group if spec['port']==root_port)
            if c['source_scope']!=scope:return False
            local=decode_scope(view,scope,c['inventory'])
            if not verify_organization_inventory(local):return False
            response=c['response']
            if not verify_channel_response(local,before,action,response,budget):return False
            blocks=set()
            for partition in c['roles']['partitions']:
                for block in partition['blocks']:
                    if root in block:blocks.add(tuple(block))
            alternatives=[]
            for block in sorted(blocks):
                candidates=[r for r in c['roles']['role_candidates'] if r['ports']==list(block)]
                if len(candidates)!=1:return False
                alternatives.append({'ports':list(block),'eligible':candidates[0]['eligible']})
            ready=bool(alternatives) and all(a['eligible'] for a in alternatives) and response['status']=='RESOLVED'
            expected={'status':'ROLE_STRUCTURAL_RESOLUTION' if ready else 'UNRESOLVED','output':response['output'] if ready else []}
            return canonical(c['role_alternatives'])==canonical(alternatives) and canonical(c['result'])==canonical(expected)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

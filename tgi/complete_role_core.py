"""All-row complete measured columns; parent uncertainty remains authoritative."""
from copy import deepcopy
from .organization_snapshot import snapshot
from .intervention_roles import certify_intervention_roles
from .intervention_resolution import certify_intervention_resolution
from .intervention_scope import decode_scope
from .role_work import RoleSearchBudget
from .identity import encode


def projected_domain(view, groups, measurements, ports):
    """Neutral projection of original evidence, never an organization inventory."""
    selected=set(ports)
    gs=[[deepcopy(s) for s in group if s['port'] in selected] for group in groups]
    sources=sorted(s['source'] for group in gs for s in group)
    ms=[deepcopy(r) for r in measurements if r['source'] in set(sources)]
    local=decode_scope(view,sources,{'active':[],'rejected':[]})
    return local,gs,ms,sources


def certify_complete_role_core(model,groups,measurements,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume();view=snapshot(model)
        parent=certify_intervention_roles(view,groups,measurements)
        columns=[]
        for i,p in enumerate(parent['ports']):
            budget.consume_many(len(parent['rows'])+1)
            if all(r['cells'][i] is not None for r in parent['rows']):columns.append(i)
        ports=[parent['ports'][i] for i in columns]
        local,gs,ms,sources=projected_domain(view,groups,measurements,ports)
        budget.consume_many(len(sources)+len(ms)+sum(map(len,gs))+len(gs))
        roles=certify_intervention_roles(local,gs,ms) if ports else None
        return {'policy':'complete_measured_role_core_v1','parent':parent,'columns':columns,
                'ports':ports,'excluded':[p for p in parent['ports'] if p not in ports],
                'groups':gs,'sources':sources,'roles':roles,
                'result':{'status':'COMPLETE_ROLE_CORE' if ports else 'NO_COMPLETE_ROLE_CORE','rows_retained':len(parent['rows'])}}


def certify_complete_core_resolution(model,groups,measurements,root_port,before,action,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume();view=snapshot(model)
        if not all(isinstance(x,str) and x for x in (root_port,before,action)):raise ValueError('Nonempty original query required')
        for x in (root_port,before,action):encode(x)
        core=certify_complete_role_core(view,groups,measurements)
        if root_port not in core['parent']['ports']:raise ValueError('Unknown root port')
        child=None
        if root_port in core['ports']:
            local,gs,ms,_=projected_domain(view,groups,measurements,core['ports'])
            child=certify_intervention_resolution(local,gs,ms,root_port,before,action)
        result={'status':'ROOT_NOT_COMPLETE','output':[]} if child is None else deepcopy(child['result'])
        return {'policy':'complete_role_core_resolution_v1','core':core,'root_port':root_port,'prefix':[before,action],'resolution':child,'result':result}

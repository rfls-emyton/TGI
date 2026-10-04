"""All original root-present observations; full parent uncertainty stays bound."""
from copy import deepcopy
from .organization_snapshot import snapshot
from .compact_role_observation import certify_compact_role_constraints
from .complete_role_core import projected_domain
from .intervention_roles import certify_intervention_roles
from .intervention_resolution import certify_intervention_resolution
from .role_work import RoleSearchBudget
from .identity import encode


def observation_domain(view,groups,measurements,row_indices,ports):
    """Neutral original-occurrence projection; no inference or truth decision."""
    return projected_domain(view,[groups[i] for i in row_indices],measurements,ports)


def certify_observed_role_core_resolution(model,groups,measurements,root_port,before,action,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume();view=snapshot(model);groups,measurements=deepcopy((groups,measurements))
        if not all(isinstance(x,str) and x for x in (root_port,before,action)):raise ValueError('Nonempty original query required')
        for x in (root_port,before,action):encode(x)
        parent=certify_compact_role_constraints(view,groups,measurements)
        if root_port not in parent['ports']:raise ValueError('Unknown root port')
        rows=[]
        for i,g in enumerate(groups):
            budget.consume_many(len(g)+1)
            if any(s['port']==root_port for s in g):rows.append(i)
        columns=[]
        for j in range(len(parent['ports'])):
            budget.consume_many(len(rows)+1)
            if all(parent['rows'][i]['cells'][j] is not None for i in rows):columns.append(j)
        ports=[parent['ports'][j] for j in columns]
        local,gs,ms,sources=observation_domain(view,groups,measurements,rows,ports)
        budget.consume_many(len(sources)+len(ms)+sum(map(len,gs))+len(gs))
        roles=certify_intervention_roles(local,gs,ms) if ports else None
        root_sources=sorted(s['source'] for g in groups for s in g if s['port']==root_port)
        core={'policy':'observed_complete_role_core_v1','parent':parent,'root_port':root_port,'row_indices':rows,'columns':columns,'ports':ports,'excluded':[p for p in parent['ports'] if p not in ports],'groups':gs,'sources':sources,'root_sources':root_sources,'roles':roles,'result':{'status':'COMPLETE_OBSERVED_ROLE_CORE' if root_port in ports else 'ROOT_NOT_COMPLETE','rows_retained':len(rows),'outside_rows_retained':len(groups)-len(rows)}}
        child=certify_intervention_resolution(local,gs,ms,root_port,before,action) if root_port in ports else None
        result={'status':'ROOT_NOT_COMPLETE','output':[]} if child is None else deepcopy(child['result'])
        return {'policy':'observed_role_core_resolution_v1','core':core,'root_port':root_port,'prefix':[before,action],'resolution':child,'result':result}

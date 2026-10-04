"""Independent all-occurrence scope, full attribution and native child checker."""
from .organization_snapshot import snapshot
from .compact_role_observation_check import verify_compact_role_constraints
from .intervention_roles_check import verify_intervention_roles
from .intervention_resolution_check import verify_intervention_resolution
from .observed_role_core import observation_domain
from .frame_engine import canonical
from .role_work import RoleSearchBudget
from .identity import encode


def verify_observed_role_core_resolution(model,groups,measurements,root_port,before,action,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            c=certificate;view=snapshot(model)
            if not all(isinstance(x,str) and x for x in (root_port,before,action)):return False
            for x in (root_port,before,action):encode(x)
            if c.get('policy') in ('complete_role_core_resolution_v1','complete_role_core_resolution_v2'):
                from .compact_complete_role_core_check import verify_compact_complete_core_resolution
                return verify_compact_complete_core_resolution(view,groups,measurements,root_port,before,action,c)
            if set(c)!={'policy','core','root_port','prefix','resolution','result'} or c['policy']!='observed_role_core_resolution_v1' or c['root_port']!=root_port or c['prefix']!=[before,action]:return False
            core=c['core']
            if set(core)!={'policy','parent','root_port','row_indices','columns','ports','excluded','groups','sources','root_sources','roles','result'} or core['policy']!='observed_complete_role_core_v1' or core['root_port']!=root_port:return False
            if not verify_compact_role_constraints(view,groups,measurements,core['parent']):return False
            parent=core['parent'];ports=parent['ports']
            if root_port not in ports:return False
            rows=[];root_sources=[]
            for index,group in enumerate(groups):
                budget.consume_many(len(group)+1);present=False
                for spec in group:
                    if spec['port']==root_port:present=True;root_sources.append(spec['source'])
                if present:rows.append(index)
            columns=[]
            for j in range(len(ports)):
                budget.consume_many(len(rows)+1);known=True
                for index in rows:
                    if parent['rows'][index]['cells'][j] is None:known=False
                if known:columns.append(j)
            selected=[ports[j] for j in columns]
            if canonical(core['row_indices'])!=canonical(rows) or canonical(core['columns'])!=canonical(columns) or core['ports']!=selected or core['excluded']!=[p for p in ports if p not in selected] or core['root_sources']!=sorted(root_sources):return False
            local,gs,ms,sources=observation_domain(view,groups,measurements,rows,selected)
            budget.consume_many(len(sources)+len(ms)+sum(map(len,gs))+len(gs))
            if canonical(core['groups'])!=canonical(gs) or core['sources']!=sources:return False
            if selected:
                if not verify_intervention_roles(local,gs,ms,core['roles']):return False
            elif core['roles'] is not None:return False
            expected={'status':'COMPLETE_OBSERVED_ROLE_CORE' if root_port in selected else 'ROOT_NOT_COMPLETE','rows_retained':len(rows),'outside_rows_retained':len(groups)-len(rows)}
            if canonical(core['result'])!=canonical(expected):return False
            if root_port not in selected:return c['resolution'] is None and canonical(c['result'])==canonical({'status':'ROOT_NOT_COMPLETE','output':[]})
            if not verify_intervention_resolution(local,gs,ms,root_port,before,action,c['resolution']) or c['resolution']['source_scope']!=sorted(root_sources):return False
            return canonical(c['result'])==canonical(c['resolution']['result'])
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

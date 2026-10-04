"""Independent full parent, maximal columns and native resolution verification."""
from .organization_snapshot import snapshot
from .intervention_roles_check import verify_intervention_roles
from .compact_role_observation_check import verify_compact_role_constraints
from .complete_role_core_check import verify_complete_role_core
from .intervention_resolution_check import verify_intervention_resolution
from .complete_role_core import projected_domain
from .frame_engine import canonical
from .role_work import RoleSearchBudget
from .identity import encode


def verify_compact_complete_role_core(model,groups,measurements,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            c=certificate;view=snapshot(model)
            if c.get('policy')=='complete_measured_role_core_v1':return verify_complete_role_core(view,groups,measurements,c)
            if set(c)!={'policy','parent','columns','ports','excluded','groups','sources','roles','result'} or c['policy']!='complete_measured_role_core_v2':return False
            if not verify_compact_role_constraints(view,groups,measurements,c['parent']):return False
            ports=c['parent']['ports'];columns=[]
            for index in range(len(ports)):
                budget.consume_many(len(c['parent']['rows'])+1)
                missing=False
                for row in c['parent']['rows']:
                    if row['cells'][index] is None:missing=True
                if not missing:columns.append(index)
            selected=[ports[i] for i in columns]
            if canonical(c['columns'])!=canonical(columns) or c['ports']!=selected or c['excluded']!=[p for p in ports if p not in selected]:return False
            local,gs,ms,sources=projected_domain(view,groups,measurements,selected)
            budget.consume_many(len(sources)+len(ms)+sum(map(len,gs))+len(gs))
            if canonical(c['groups'])!=canonical(gs) or c['sources']!=sources:return False
            if selected:
                if not verify_intervention_roles(local,gs,ms,c['roles']):return False
            elif c['roles'] is not None:return False
            expected={'status':'COMPLETE_ROLE_CORE' if selected else 'NO_COMPLETE_ROLE_CORE','rows_retained':len(groups)}
            return canonical(c['result'])==canonical(expected)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False


def verify_compact_complete_core_resolution(model,groups,measurements,root_port,before,action,certificate,*,max_search_steps=None):
    from .complete_role_core_check import verify_complete_core_resolution
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            c=certificate;view=snapshot(model)
            if not all(isinstance(x,str) and x for x in (root_port,before,action)):return False
            for x in (root_port,before,action):encode(x)
            if c.get('policy')=='observed_role_core_resolution_v1':
                from .observed_role_core_check import verify_observed_role_core_resolution
                return verify_observed_role_core_resolution(view,groups,measurements,root_port,before,action,c)
            if c.get('policy')=='complete_role_core_resolution_v1':return verify_complete_core_resolution(view,groups,measurements,root_port,before,action,c)
            if set(c)!={'policy','core','root_port','prefix','resolution','result'} or c['policy']!='complete_role_core_resolution_v2' or c['root_port']!=root_port or c['prefix']!=[before,action]:return False
            if not verify_compact_complete_role_core(view,groups,measurements,c['core']) or root_port not in c['core']['parent']['ports']:return False
            if root_port not in c['core']['ports']:
                return c['resolution'] is None and canonical(c['result'])==canonical({'status':'ROOT_NOT_COMPLETE','output':[]})
            local,gs,ms,_=projected_domain(view,groups,measurements,c['core']['ports'])
            if not verify_intervention_resolution(local,gs,ms,root_port,before,action,c['resolution']):return False
            return canonical(c['result'])==canonical(c['resolution']['result'])
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

"""Exact full original binary role domain without enumerating its completions."""
from copy import deepcopy
from .organization_snapshot import snapshot
from .intervention_roles import _cells
from .role_work import RoleSearchBudget


def certify_compact_role_constraints(model,groups,measurements,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume();groups,measurements=deepcopy((groups,measurements));witness,ports,rows,diversity=_cells(snapshot(model),groups,measurements)
        budget.consume_many(sum(len(r['cells']) for r in rows));free=sum(x is None for r in rows for x in r['cells'])
        return {'policy':'compact_visible_role_constraints_v1','groups':groups,'witness':witness,'ports':ports,'rows':rows,'changed_before_diversity':diversity,'completions':{'base':2,'exponent':free},'status':'UNCERTAIN_ATTRIBUTION' if free else 'DETERMINED_VISIBLE_ROLES'}

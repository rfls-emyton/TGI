"""Native sequence plans explicitly bound to their complete measured parent."""
from copy import deepcopy
from .organization_snapshot import snapshot
from .compact_complete_role_core_check import verify_compact_complete_role_core
from .complete_role_core import projected_domain
from .intervention_sequence_experiment import certify_intervention_sequence_experiments
from .role_work import RoleSearchBudget


def certify_scoped_sequence_experiments(model,groups,measurements,seed,max_depth,core,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume();view=snapshot(model)
        groups,measurements,core=deepcopy((groups,measurements,core))
        if core.get('policy')!='complete_measured_role_core_v2' or not verify_compact_complete_role_core(view,groups,measurements,core) or not core['ports']:
            raise ValueError('Verified nonempty maximal complete core required')
        local,gs,ms,sources=projected_domain(view,groups,measurements,core['ports'])
        budget.consume_many(len(sources)+len(ms)+sum(map(len,gs))+len(gs))
        plan=certify_intervention_sequence_experiments(local,gs,ms,seed,max_depth)
        return {**plan,'policy':'native_scoped_sequence_experiment_v1','scope':core}

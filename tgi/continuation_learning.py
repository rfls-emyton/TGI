"""Native immutable experience-to-knowledge transaction after actual continuation."""
from copy import deepcopy
from .organization_snapshot import snapshot
from .identity import decode
from .sequence_prefix_feedback_check import verify_sequence_continuation
from .joint_frontier_acquisition import _rebuild
from .compact_complete_role_core import certify_compact_complete_role_core as certify_complete_role_core
from .scoped_sequence_experiment import certify_scoped_sequence_experiments
from .role_work import RoleSearchBudget
from .incremental import FormationSearchLimit


def prepare_continuation_learning(model,groups,measurements,seed,max_depth,plan,previous,previous_groups,previous_measurements,previous_sources,prior,acquisition,acquired_groups,observed_measurements,sources,continuation,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume();v=deepcopy((groups,measurements,seed,max_depth,plan,previous_groups,previous_measurements,previous_sources,prior,acquired_groups,observed_measurements,sources,continuation));groups,measurements,seed,max_depth,plan,previous_groups,previous_measurements,previous_sources,prior,acquired_groups,observed_measurements,sources,continuation=v
        model,previous,acquisition=snapshot(model),snapshot(previous),snapshot(acquisition)
        context=(model,groups,measurements,seed,max_depth,plan,previous,previous_groups,previous_measurements,previous_sources,prior,acquisition,acquired_groups,observed_measurements,sources)
        if not verify_sequence_continuation(*context,continuation):raise ValueError('Invalid or stale original continuation')
        admitted=continuation['result']['observation_admitted'];after=None;history=None;core=None;renewed=None;newseed=None
        if admitted:
            after,history=_rebuild(model,groups,measurements,acquisition,acquired_groups,observed_measurements,budget)
            limits=[];current=budget
            while current is not None:
                if current.limit is not None:limits.append(current.limit-current.used)
                current=getattr(current,'parent',None)
            try:after.form(max_search_steps=min(limits) if limits else None)
            except FormationSearchLimit as error:
                budget.consume_many(error.used);budget.consume();raise
            budget.consume_many(after.formation_work['search_steps'])
            core=certify_complete_role_core(after,history['groups'],history['measurements'])
            newseed=decode(acquisition.episodes[sources[-1]][0][2])
            if core['ports']:
                renewed=certify_scoped_sequence_experiments(after,history['groups'],history['measurements'],newseed,max_depth,core)
        result={'status':'CONTINUATION_EXPERIENCE_LEARNED' if admitted else 'CONTINUATION_NOT_ADMITTED','experience_admitted':admitted,'renewed_status':None if not admitted else 'NO_COMPLETE_ROLE_CORE' if renewed is None else renewed['result']['status']}
        return after,{'policy':'native_continuation_learning_v1','continuation':continuation,'history':history,'core':core,'renewed_seed':newseed,'renewed':renewed,'result':result}

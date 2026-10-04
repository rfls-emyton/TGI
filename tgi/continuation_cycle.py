"""Neutral owned lifecycle over independently verified native continuation."""
from copy import deepcopy
from .organization_snapshot import snapshot
from .organization_inventory_check import verify_organization_inventory
from .intervention_sequence_experiment_check import verify_intervention_sequence_experiments
from .sequence_prefix_feedback import certify_sequence_prefix_observation,certify_sequence_continuation
from .sequence_prefix_feedback_check import verify_sequence_prefix_observation,verify_sequence_continuation
from .continuation_learning import prepare_continuation_learning
from .continuation_learning_check import verify_continuation_learning
from .continuation_checkpoint import save_continuation_checkpoint,load_continuation_checkpoint
from .compact_complete_role_core import certify_compact_complete_role_core
from .scoped_sequence_experiment_check import verify_scoped_sequence_experiments
from .role_work import RoleSearchBudget


class ContinuationCycle:
    """Own full formed evidence; independently check before creating a successor."""
    def __init__(self,model,groups,measurements,seed,max_depth,plan,*,max_search_steps=None):
        budget=RoleSearchBudget(max_search_steps)
        with budget.scope():
            budget.consume();owned=deepcopy((model,groups,measurements,seed,max_depth,plan))
            if not verify_organization_inventory(snapshot(owned[0])) or not verify_intervention_sequence_experiments(*owned):
                raise ValueError('Verified full-history plan and native knowledge inventory required')
            self._cycle=owned;self._transaction=None

    def context(self):
        """Return an owned copy of (model,groups,measurements,seed,depth,plan)."""
        return deepcopy(self._cycle)

    @property
    def status(self):
        plan=self._cycle[5]
        return 'NO_COMPLETE_ROLE_CORE' if plan is None else plan['result']['status']

    @classmethod
    def from_transaction(cls,context,after,certificate,*,upgrade_legacy_scope=False,max_search_steps=None):
        budget=RoleSearchBudget(max_search_steps)
        with budget.scope():
            budget.consume()
            if type(upgrade_legacy_scope) is not bool:raise ValueError('Explicit boolean legacy scope upgrade required')
            context,after,c=deepcopy((context,after,certificate))
            if not verify_continuation_learning(*context,after,c) or not c['result']['experience_admitted']:
                raise ValueError('Verified admitted complete transaction required')
            plan=deepcopy(c['renewed']);history=c['history'];depth=context[4];seed=c['renewed_seed']
            if plan is not None and plan['policy']=='native_sequence_experiment_v1':
                if not upgrade_legacy_scope:raise ValueError('Explicit legacy scope upgrade required')
                core=certify_compact_complete_role_core(after,history['groups'],history['measurements'])
                plan={**plan,'policy':'native_scoped_sequence_experiment_v1','scope':core}
                if not verify_scoped_sequence_experiments(after,history['groups'],history['measurements'],seed,depth,plan):
                    raise ValueError('Legacy scope upgrade verification failed')
            obj=cls.__new__(cls)
            obj._cycle=(after,deepcopy(history['groups']),deepcopy(history['measurements']),seed,depth,plan)
            obj._transaction=(context,after,c)
            return obj

    def prefix(self,acquisition,groups,measurements,sources,*,max_search_steps=None):
        budget=RoleSearchBudget(max_search_steps)
        with budget.scope():
            budget.consume()
            if self._cycle[5] is None:raise ValueError('NO_COMPLETE_ROLE_CORE')
            args=(*self._cycle,acquisition,groups,measurements,sources)
            c=certify_sequence_prefix_observation(*args)
            if not verify_sequence_prefix_observation(*args,c):raise ValueError('Native prefix verification failed')
            return c

    def advance(self,previous,previous_groups,previous_measurements,previous_sources,prior,acquisition,acquired_groups,observed_measurements,sources,*,max_search_steps=None):
        budget=RoleSearchBudget(max_search_steps)
        with budget.scope():
            budget.consume()
            if self._cycle[5] is None:raise ValueError('NO_COMPLETE_ROLE_CORE')
            context=(*self._cycle,previous,previous_groups,previous_measurements,previous_sources,prior,acquisition,acquired_groups,observed_measurements,sources)
            continuation=certify_sequence_continuation(*context)
            if not verify_sequence_continuation(*context,continuation):raise ValueError('Native continuation verification failed')
            transaction=(*context,continuation);after,c=prepare_continuation_learning(*transaction)
            if not verify_continuation_learning(*transaction,after,c):raise ValueError('Native knowledge transaction verification failed')
            if not c['result']['experience_admitted']:return None,c
            return type(self).from_transaction(transaction,after,c),c

    def commit(self,path,*,max_search_steps=None):
        if self._transaction is None:raise ValueError('Admitted transaction required for commit')
        context,after,c=self._transaction
        return save_continuation_checkpoint(path,context,after,c,max_search_steps=max_search_steps)

    @classmethod
    def recover(cls,path,expected_sha256,*,upgrade_legacy_scope=False,max_search_steps=None):
        budget=RoleSearchBudget(max_search_steps)
        with budget.scope():
            budget.consume();context,after,c=load_continuation_checkpoint(path,expected_sha256)
            return cls.from_transaction(context,after,c,upgrade_legacy_scope=upgrade_legacy_scope)


    def resolve(self,root_port,before,action,*,max_search_steps=None):
        """Full-parent bound knowledge query, independent of experiment selection."""
        from .observed_role_core import certify_observed_role_core_resolution
        from .observed_role_core_check import verify_observed_role_core_resolution
        budget=RoleSearchBudget(max_search_steps)
        with budget.scope():
            budget.consume();model,groups,measurements=self._cycle[:3]
            args=(model,groups,measurements,root_port,before,action)
            c=certify_observed_role_core_resolution(*args)
            if not verify_observed_role_core_resolution(*args,c):raise ValueError('Native complete-core resolution verification failed')
            return c

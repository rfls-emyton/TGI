"""Endogenous role conditioned channel transformations on original crystal paths."""
from copy import deepcopy
from dataclasses import asdict
from .identity import encode
from .organization import RawOrganization
from .organization_snapshot import snapshot
from .intervention_roles import certify_intervention_roles
from .role_work import RoleSearchBudget
from .incremental import FormationSearchLimit


def certify_intervention_resolution(acquisition, groups, measurements, root_port, before, action, *, max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        if not all(isinstance(x,str) and x for x in (root_port,before,action)):raise ValueError('Nonempty original query required')
        for x in (root_port,before,action):encode(x)
        view=snapshot(acquisition);groups,measurements=deepcopy(groups),deepcopy(measurements)
        roles=certify_intervention_roles(view,groups,measurements)
        if root_port not in roles['ports']:raise ValueError('Unknown root port')
        index=roles['ports'].index(root_port)
        sources=sorted(spec['source'] for group in groups for spec in group if spec['port']==root_port)
        local=RawOrganization();local.frames=view.frames;local.episodes={s:view.episodes[s] for s in sources}
        # Formation owns a SearchBudget; bound it by every inherited remainder,
        # then debit exactly its measured steps to the enclosing role budget.
        limits=[];current=budget
        while current is not None:
            if current.limit is not None:limits.append(current.limit-current.used)
            current=getattr(current,'parent',None)
        try:
            local.form(max_search_steps=min(limits) if limits else None)
        except FormationSearchLimit as error:
            for _ in range(error.used):budget.consume()
            budget.consume()  # raises at the actual exhausted enclosing boundary
            raise
        for _ in range(local.formation_work['search_steps']):budget.consume()
        inventory={'active':[asdict(h) for _,h in sorted(local.organizations.items())],
                   'rejected':[{'organization':asdict(h),'oppositions':[asdict(o) for o in opposing]} for _,(h,opposing) in sorted(local.rejected_organizations.items())]}
        response=local.resolve([before,action],terminal_only=True)
        blocks=sorted({tuple(b) for p in roles['partitions'] for b in p['blocks'] if index in b})
        alternatives=[{'ports':list(b),'eligible':next(c['eligible'] for c in roles['role_candidates'] if c['ports']==list(b))} for b in blocks]
        available=bool(alternatives) and all(b['eligible'] for b in alternatives) and response['status']=='RESOLVED'
        return {'policy':'intervention_structural_resolution_v1','roles':roles,'root_port':root_port,'prefix':[before,action],
                'source_scope':sources,'inventory':inventory,'response':response,'role_alternatives':alternatives,
                'result':{'status':'ROLE_STRUCTURAL_RESOLUTION' if available else 'UNRESOLVED','output':response['output'] if available else []}}

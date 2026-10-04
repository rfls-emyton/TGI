"""All measured before-context alternatives; original-scope recrystallization."""
from copy import deepcopy
from dataclasses import asdict
from itertools import combinations
from .organization import RawOrganization
from .acquisition_snapshot import acquisition_snapshot as snapshot
from .acquisition_witness import certify_raw_acquisition_witness as certify_acquisition_witness
from .measured_context_layout import layout,query_values
from .role_work import RoleSearchBudget
from .incremental import FormationSearchLimit


def certify_measured_context(model,groups,measurements,root_port,before,action,context,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume();groups,measurements,context=deepcopy((groups,measurements,context));view=snapshot(model)
        witness=certify_acquisition_witness(view,measurements);ports,rows=layout(view,groups,measurements,root_port,budget);query_values(ports,root_port,before,action,context)
        others=[p for p in ports if p!=root_port];conflicts=[]
        for i,j in combinations(range(len(rows)),2):
            budget.consume();a,b=rows[i]['cells'][root_port]['frames'],rows[j]['cells'][root_port]['frames']
            if a[:2]==b[:2] and a[2]!=b[2]:conflicts.append([i,j])
        candidates=[];scopes={};certain=all(row['certain'] for row in rows)
        for mask in range(1<<len(others)):
            budget.consume();selected=[p for i,p in enumerate(others) if mask>>i&1];blocked=[]
            for i,j in conflicts:
                budget.consume()
                if all(rows[i]['cells'][p]['frames'][0]==rows[j]['cells'][p]['frames'][0] for p in selected):blocked.append([i,j])
            query_blocked=[pair for pair in blocked if all(rows[pair[0]]['cells'][p]['frames'][0]==context[p] for p in selected)];compatible=not query_blocked;scope=[];inventory=None;response=None
            if compatible and certain:
                for row in rows:
                    budget.consume()
                    if all(row['cells'][p]['frames'][0]==context[p] for p in selected):scope.append(row['cells'][root_port]['source'])
                scope.sort();key=tuple(scope)
                if scope and key not in scopes:
                    local=RawOrganization();local.frames=view.frames;local.episodes={s:view.episodes[s] for s in scope}
                    limits=[];current=budget
                    while current is not None:
                        if current.limit is not None:limits.append(current.limit-current.used)
                        current=getattr(current,'parent',None)
                    try:local.form(max_search_steps=min(limits) if limits else None)
                    except FormationSearchLimit as error:
                        for _ in range(error.used):budget.consume()
                        budget.consume();raise
                    for _ in range(local.formation_work['search_steps']):budget.consume()
                    inventory={'active':[asdict(h) for _,h in sorted(local.organizations.items())],'rejected':[{'organization':asdict(h),'oppositions':[asdict(o) for o in os]} for _,(h,os) in sorted(local.rejected_organizations.items())]}
                    scopes[key]=(inventory,local.resolve([before,action],terminal_only=True))
                if scope:inventory,response=deepcopy(scopes[key])
            candidates.append({'ports':selected,'blocked_pairs':blocked,'query_blocked_pairs':query_blocked,'compatible':compatible,'source_scope':scope,'inventory':inventory,'response':response})
        alternatives=[c for c in candidates if c['compatible']];outputs={tuple(c['response']['output']) for c in alternatives if c['response'] is not None and c['response']['status']=='RESOLVED'}
        ready=certain and bool(alternatives) and all(c['response'] is not None and c['response']['status']=='RESOLVED' for c in alternatives) and len(outputs)==1
        status='CONTEXTUAL_STRUCTURAL_RESOLUTION' if ready else 'INCOMPLETE_OBSERVATION' if not certain else 'NO_OBSERVED_CONTEXT_SEPARATOR' if not alternatives else 'UNRESOLVED_CONTEXT_ALTERNATIVES'
        return {'policy':'measured_context_recrystallization_v1','groups':groups,'witness':witness,'root_port':root_port,'prefix':[before,action],'context':context,'ports':ports,'rows':rows,'conflict_pairs':conflicts,'candidates':candidates,'result':{'status':status,'output':list(next(iter(outputs))) if ready else [],'compatible_contexts':[c['ports'] for c in alternatives]}}

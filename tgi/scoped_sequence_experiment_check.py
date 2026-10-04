"""Independent full-parent and exact original-source plan scope verifier."""
from copy import deepcopy
from .organization_snapshot import snapshot
from .compact_complete_role_core_check import verify_compact_complete_role_core
from .intervention_scope import decode_scope
from .frame_engine import canonical
from .role_work import RoleSearchBudget


def verify_scoped_sequence_experiments(model,groups,measurements,seed,max_depth,certificate,*,max_search_steps=None):
    from .intervention_sequence_experiment_check import verify_intervention_sequence_experiments
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            view=snapshot(model);c=deepcopy(certificate)
            if set(c)!={'policy','seed','max_depth','roles','classes','rows','result','scope'} or c['policy']!='native_scoped_sequence_experiment_v1':return False
            core=c['scope']
            if core['policy']!='complete_measured_role_core_v2' or not core['ports'] or not verify_compact_complete_role_core(view,groups,measurements,core):return False
            selected=set(core['ports']);gs=[];source_names=[]
            for group in groups:
                budget.consume_many(len(group)+1)
                row=[deepcopy(x) for x in group if x['port'] in selected];gs.append(row);source_names.extend(x['source'] for x in row)
            source_names=sorted(source_names);source_set=set(source_names);ms=[]
            for row in measurements:
                budget.consume()
                if row['source'] in source_set:ms.append(deepcopy(row))
            budget.consume_many(len(source_names))
            if canonical(gs)!=canonical(core['groups']) or canonical(source_names)!=canonical(core['sources']):return False
            local=decode_scope(view,source_names,{'active':[],'rejected':[]})
            plain={k:v for k,v in c.items() if k!='scope'};plain['policy']='native_sequence_experiment_v1'
            return verify_intervention_sequence_experiments(local,gs,ms,seed,max_depth,plain)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

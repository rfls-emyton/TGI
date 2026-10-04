"""All endogenous minimal context laws on original structural and crystal paths."""
from copy import deepcopy
from dataclasses import asdict
from itertools import combinations
from .organization import RawOrganization
from .acquisition_snapshot import acquisition_snapshot
from .acquisition_witness import certify_raw_acquisition_witness
from .measured_context_layout import layout,query_values
from .incidence import _endpoint
from .identity import decode
from .role_work import RoleSearchBudget
from .incremental import FormationSearchLimit


def certify_measured_context_laws(model,groups,measurements,root_port,before,action,context,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume();groups,measurements,context=deepcopy((groups,measurements,context));view=acquisition_snapshot(model)
        inventories=[sorted(spec['port'] for spec in g) for g in groups] if isinstance(groups,list) and all(isinstance(g,list) and all(isinstance(spec,dict) and 'port' in spec for spec in g) for g in groups) else []
        if inventories and any(p!=inventories[0] for p in inventories):
            from .observation_context_laws import certify_observation_context_laws
            return certify_observation_context_laws(view,groups,measurements,root_port,before,action,context)
        witness=certify_raw_acquisition_witness(view,measurements);ports,rows=layout(view,groups,measurements,root_port,budget);query_values(ports,root_port,before,action,context)
        others=[p for p in ports if p!=root_port];conflicts=[];unseparated=[];differences=[]
        for i,j in combinations(range(len(rows)),2):
            budget.consume();a,b=rows[i]['cells'][root_port]['frames'],rows[j]['cells'][root_port]['frames']
            if a[1]!=action or a[:2]!=b[:2] or a[2]==b[2]:continue
            different=[p for p in others if rows[i]['cells'][p]['frames'][0]!=rows[j]['cells'][p]['frames'][0]]
            conflicts.append({'left':i,'right':j,'different_ports':different})
            if different:differences.append(frozenset(different))
            else:unseparated.append([i,j])
        families={frozenset()}
        for different in differences:
            next_sets=set()
            for selected in families:
                budget.consume()
                if selected & different:next_sets.add(selected)
                else:
                    for port in sorted(different):budget.consume();next_sets.add(selected|{port})
            families=set()
            for selected in next_sets:
                budget.consume()
                if not any(other<selected for other in next_sets):families.add(selected)
        minimal=sorted((sorted(selected) for selected in families));certain=all(row['certain'] for row in rows)
        local_conflicts=[pair for pair in unseparated if rows[pair[0]]['cells'][root_port]['frames'][0]==before and all(rows[pair[0]]['cells'][p]['frames'][0]==context[p] for p in others)]
        candidates=[];outputs=set();all_ready=True
        for selected in minimal:
            budget.consume();scope=[];inventory=None;response=None;literal=[];conclusions=[]
            if certain:
                for row in rows:
                    budget.consume()
                    if row['cells'][root_port]['frames'][1]==action and all(row['cells'][p]['frames'][0]==context[p] for p in selected):scope.append(row['cells'][root_port]['source'])
                scope.sort()
            if scope:
                local=RawOrganization();local.frames=view.frames;local.episodes={s:view.episodes[s] for s in scope};limits=[];current=budget
                while current is not None:
                    if current.limit is not None:limits.append(max(0,current.limit-current.used))
                    current=getattr(current,'parent',None)
                try:local.form(max_search_steps=min(limits) if limits else None)
                except FormationSearchLimit as error:budget.consume_many(error.used);budget.consume();raise
                budget.consume_many(local.formation_work['search_steps'])
                inventory={'active':[asdict(h) for _,h in sorted(local.organizations.items())],'rejected':[{'organization':asdict(h),'oppositions':[asdict(o) for o in os]} for _,(h,os) in sorted(local.rejected_organizations.items())]}
                response=local.resolve([before,action],terminal_only=True);values={tuple(x) for x in response['candidates']}
                for source in scope:
                    budget.consume();frames=view.episodes[source][0]
                    if [decode(frames[0]),decode(frames[1])]==[before,action]:
                        value=decode(frames[2]);literal.append({'source':source,'output':value,'occurrence':_endpoint(view,source,(2,0,len(frames[2])))});values.add((value,))
                conclusions=[list(value) for value in sorted(values)]
            resolved=bool(scope) and response['status']!='INCOMPLETE' and len(conclusions)==1
            all_ready &= resolved
            if resolved:outputs.add(tuple(conclusions[0]))
            candidates.append({'ports':selected,'source_scope':scope,'inventory':inventory,'structural_response':response,'crystal_paths':literal,'conclusions':conclusions,'resolved':bool(resolved)})
        ready=certain and not local_conflicts and bool(candidates) and all_ready and len(outputs)==1
        status='MEASURED_CONTEXT_LAW_RESOLVED' if ready else 'INCOMPLETE_OBSERVATION' if not certain else 'CONTRADICTED_ORIGINAL_INPUT' if local_conflicts else 'UNRESOLVED_CONTEXT_LAWS'
        return {'policy':'measured_context_laws_v1','groups':groups,'witness':witness,'root_port':root_port,'prefix':[before,action],'context':context,'ports':ports,'rows':rows,'conflicts':conflicts,'unseparated_conflicts':unseparated,'local_conflicts':local_conflicts,'minimal_families':minimal,'candidates':candidates,'result':{'status':status,'output':list(next(iter(outputs))) if ready else []}}

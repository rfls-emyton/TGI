"""Every original root occurrence with explicit common observed contexts."""
from copy import deepcopy
from .acquisition_snapshot import acquisition_snapshot
from .acquisition_witness import certify_raw_acquisition_witness
from .measured_context_layout import layout,query_values
from .intervention_scope import decode_scope
from .frame_engine import canonical
from .role_work import RoleSearchBudget


def projected_observations(view,groups,measurements,indices,ports):
    """Neutral original-source projection, no inference or state fabrication."""
    selected=set(ports);gs=[[deepcopy(s) for s in groups[i] if s['port'] in selected] for i in indices];sources=sorted(s['source'] for g in gs for s in g);source_set=set(sources);ms=[deepcopy(r) for r in measurements if r['source'] in source_set]
    return decode_scope(view,sources,{'active':[],'rejected':[]}),gs,ms,sources


def certify_observation_context_laws(model,groups,measurements,root_port,before,action,context,*,max_search_steps=None):
    from .measured_context_laws import certify_measured_context_laws
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume();view=acquisition_snapshot(model);groups,measurements,context=deepcopy((groups,measurements,context));witness=certify_raw_acquisition_witness(view,measurements);ports,rows=layout(view,groups,measurements,root_port,budget,allow_partial=True);query_values(ports,root_port,before,action,context)
        indices=[]
        for i,row in enumerate(rows):
            budget.consume()
            if root_port in row['cells']:indices.append(i)
        common=[]
        for p in ports:
            budget.consume_many(len(indices)+1)
            if all(p in rows[i]['cells'] for i in indices):common.append(p)
        local,gs,ms,sources=projected_observations(view,groups,measurements,indices,common);budget.consume_many(len(sources)+len(ms)+sum(map(len,gs))+len(gs));child_context={p:context[p] for p in common if p!=root_port};law=certify_measured_context_laws(local,gs,ms,root_port,before,action,child_context)
        certain=all(rows[i]['certain'] for i in indices);result=deepcopy(law['result']) if certain else {'status':'INCOMPLETE_OBSERVATION','output':[]}
        return {'policy':'observation_context_laws_v1','parent':{'groups':groups,'witness':witness,'ports':ports,'rows':rows},'root_port':root_port,'prefix':[before,action],'context':context,'row_indices':indices,'ports':common,'groups':gs,'source_scope':sources,'law':law,'candidates':deepcopy(law['candidates']),'result':result}

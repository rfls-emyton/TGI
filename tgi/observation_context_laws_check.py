"""Independent full-parent, all-root projection and native context-law check."""
from .acquisition_snapshot import acquisition_snapshot
from .acquisition_witness import verify_raw_acquisition_witness
from .measured_context_layout import layout,query_values
from .observation_context_laws import projected_observations
from .frame_engine import canonical
from .role_work import RoleSearchBudget


def verify_observation_context_laws(model,groups,measurements,root_port,before,action,context,certificate,*,max_search_steps=None):
    from .measured_context_laws_check import verify_measured_context_laws
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            c=certificate;view=acquisition_snapshot(model)
            if c.get('policy')=='measured_context_laws_v1':return verify_measured_context_laws(view,groups,measurements,root_port,before,action,context,c)
            if set(c)!={'policy','parent','root_port','prefix','context','row_indices','ports','groups','source_scope','law','candidates','result'} or c['policy']!='observation_context_laws_v1' or c['root_port']!=root_port or c['prefix']!=[before,action] or canonical(c['context'])!=canonical(context):return False
            parent=c['parent']
            if set(parent)!={'groups','witness','ports','rows'} or canonical(parent['groups'])!=canonical(groups) or not verify_raw_acquisition_witness(view,measurements,parent['witness']):return False
            ports,rows=layout(view,groups,measurements,root_port,budget,allow_partial=True);query_values(ports,root_port,before,action,context)
            if parent['ports']!=ports or canonical(parent['rows'])!=canonical(rows):return False
            indices=[]
            for i,row in enumerate(rows):
                budget.consume()
                if root_port in row['cells']:indices.append(i)
            common=[]
            for port in ports:
                budget.consume_many(len(indices)+1);present=True
                for i in indices:
                    if port not in rows[i]['cells']:present=False
                if present:common.append(port)
            if canonical(c['row_indices'])!=canonical(indices) or c['ports']!=common:return False
            local,gs,ms,sources=projected_observations(view,groups,measurements,indices,common);budget.consume_many(len(sources)+len(ms)+sum(map(len,gs))+len(gs))
            if canonical(c['groups'])!=canonical(gs) or c['source_scope']!=sources:return False
            child_context={p:context[p] for p in common if p!=root_port}
            if not verify_measured_context_laws(local,gs,ms,root_port,before,action,child_context,c['law']) or canonical(c['candidates'])!=canonical(c['law']['candidates']):return False
            result=c['law']['result'] if all(rows[i]['certain'] for i in indices) else {'status':'INCOMPLETE_OBSERVATION','output':[]}
            return canonical(c['result'])==canonical(result)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

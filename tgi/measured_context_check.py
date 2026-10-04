"""Independent complete context enumeration and original crystal verification."""
from copy import deepcopy
from .acquisition_snapshot import acquisition_snapshot as snapshot
from .acquisition_witness import verify_raw_acquisition_witness as verify_acquisition_witness
from .measured_context_layout import layout,query_values
from .intervention_scope import decode_scope
from .organization_inventory_check import verify_organization_inventory
from .intervention_resolution_check import verify_channel_response
from .frame_engine import canonical
from .role_work import RoleSearchBudget


def verify_measured_context(model,groups,measurements,root_port,before,action,context,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            c=deepcopy(certificate);view=snapshot(model)
            if set(c)!={'policy','groups','witness','root_port','prefix','context','ports','rows','conflict_pairs','candidates','result'} or c['policy']!='measured_context_recrystallization_v1':return False
            if c['root_port']!=root_port or c['prefix']!=[before,action] or canonical(c['context'])!=canonical(context) or canonical(c['groups'])!=canonical(groups):return False
            if not verify_acquisition_witness(view,measurements,c['witness']):return False
            ports,rows=layout(view,groups,measurements,root_port,budget);query_values(ports,root_port,before,action,context)
            if c['ports']!=ports or canonical(c['rows'])!=canonical(rows):return False
            conflicts=[]
            for i in range(len(rows)):
                for j in range(i+1,len(rows)):
                    budget.consume();left=rows[i]['cells'][root_port]['frames'];right=rows[j]['cells'][root_port]['frames']
                    if left[0]==right[0] and left[1]==right[1] and left[2]!=right[2]:conflicts.append([i,j])
            if canonical(c['conflict_pairs'])!=canonical(conflicts):return False
            others=sorted(set(ports)-{root_port});n=1<<len(others)
            if len(c['candidates'])!=n:return False
            certain=all(row['certain'] for row in rows);checked={};alternatives=[];outputs=set();all_ready=True
            for mask,item in enumerate(c['candidates']):
                budget.consume()
                if set(item)!={'ports','blocked_pairs','query_blocked_pairs','compatible','source_scope','inventory','response'}:return False
                selected=[p for i,p in enumerate(others) if mask&(1<<i)];blocked=[]
                for pair in conflicts:
                    budget.consume();i,j=pair
                    if not any(rows[i]['cells'][p]['frames'][0]!=rows[j]['cells'][p]['frames'][0] for p in selected):blocked.append(pair)
                query_blocked=[pair for pair in blocked if all(rows[pair[0]]['cells'][p]['frames'][0]==context[p] for p in selected)];compatible=not query_blocked;scope=[]
                if compatible:
                    alternatives.append(selected)
                    if certain:
                        for row in rows:
                            budget.consume()
                            if all(context[p]==row['cells'][p]['frames'][0] for p in selected):scope.append(row['cells'][root_port]['source'])
                        scope.sort()
                if item['ports']!=selected or canonical(item['blocked_pairs'])!=canonical(blocked) or canonical(item['query_blocked_pairs'])!=canonical(query_blocked) or type(item['compatible']) is not bool or item['compatible']!=compatible or item['source_scope']!=scope:return False
                if not scope:
                    if item['inventory'] is not None or item['response'] is not None:return False
                    if compatible:all_ready=False
                    continue
                key=tuple(scope)
                if key not in checked:
                    local=decode_scope(view,scope,item['inventory'])
                    if not verify_organization_inventory(local) or not verify_channel_response(local,before,action,item['response'],budget):return False
                    checked[key]=(canonical(item['inventory']),canonical(item['response']))
                elif checked[key]!=(canonical(item['inventory']),canonical(item['response'])):return False
                if item['response']['status']=='RESOLVED':outputs.add(tuple(item['response']['output']))
                else:all_ready=False
            ready=certain and bool(alternatives) and all_ready and len(outputs)==1
            status='CONTEXTUAL_STRUCTURAL_RESOLUTION' if ready else 'INCOMPLETE_OBSERVATION' if not certain else 'NO_OBSERVED_CONTEXT_SEPARATOR' if not alternatives else 'UNRESOLVED_CONTEXT_ALTERNATIVES'
            expected={'status':status,'output':list(next(iter(outputs))) if ready else [],'compatible_contexts':alternatives}
            return canonical(c['result'])==canonical(expected)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

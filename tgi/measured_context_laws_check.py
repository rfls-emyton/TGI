"""Independent complete minimal-family and original crystal/organization checker."""
from copy import deepcopy
from .acquisition_snapshot import acquisition_snapshot
from .acquisition_witness import verify_raw_acquisition_witness
from .measured_context_layout import layout,query_values
from .intervention_scope import decode_scope
from .organization_inventory_check import verify_organization_inventory
from .intervention_resolution_check import verify_channel_response
from .identity import decode
from .frame_engine import canonical
from .role_work import RoleSearchBudget


def _minimal_conflict_families(constraints,budget):
    """Independent obligation search, complete even for unequal-size families."""
    stack=[frozenset()];visited=set();families=set()
    while stack:
        budget.consume();selected=stack.pop()
        if selected in visited:continue
        visited.add(selected);missing=None;hits=[]
        for difference in constraints:
            budget.consume();hit=selected & difference
            if not hit:missing=difference;break
            hits.append(hit)
        if missing is not None:
            for port in sorted(missing,reverse=True):
                budget.consume();stack.append(selected|{port})
        else:
            private=set()
            for hit in hits:
                budget.consume()
                if len(hit)==1:private.update(hit)
            if selected<=private:families.add(selected)
    return sorted(sorted(selected) for selected in families)


def verify_measured_context_laws(model,groups,measurements,root_port,before,action,context,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            c=deepcopy(certificate);view=acquisition_snapshot(model)
            if c.get('policy')=='observation_context_laws_v1':
                from .observation_context_laws_check import verify_observation_context_laws
                return verify_observation_context_laws(view,groups,measurements,root_port,before,action,context,c)
            if set(c)!={'policy','groups','witness','root_port','prefix','context','ports','rows','conflicts','unseparated_conflicts','local_conflicts','minimal_families','candidates','result'} or c['policy']!='measured_context_laws_v1':return False
            if c['root_port']!=root_port or c['prefix']!=[before,action] or canonical(c['context'])!=canonical(context) or canonical(c['groups'])!=canonical(groups):return False
            if not verify_raw_acquisition_witness(view,measurements,c['witness']):return False
            ports,rows=layout(view,groups,measurements,root_port,budget);query_values(ports,root_port,before,action,context)
            if c['ports']!=ports or canonical(c['rows'])!=canonical(rows):return False
            others=sorted(set(ports)-{root_port});conflicts=[];unseparated=[];constraints=[]
            for i in range(len(rows)):
                left=rows[i]['cells'][root_port]['frames']
                for j in range(i+1,len(rows)):
                    budget.consume();right=rows[j]['cells'][root_port]['frames']
                    if left[1]!=action or left[0]!=right[0] or left[1]!=right[1] or left[2]==right[2]:continue
                    diff=[p for p in others if rows[i]['cells'][p]['frames'][0]!=rows[j]['cells'][p]['frames'][0]];conflicts.append({'left':i,'right':j,'different_ports':diff})
                    if diff:constraints.append(set(diff))
                    else:unseparated.append([i,j])
            minimal=_minimal_conflict_families(constraints,budget)
            local_conflicts=[pair for pair in unseparated if rows[pair[0]]['cells'][root_port]['frames'][0]==before and all(rows[pair[0]]['cells'][p]['frames'][0]==context[p] for p in others)]
            if canonical(c['conflicts'])!=canonical(conflicts) or canonical(c['unseparated_conflicts'])!=canonical(unseparated) or canonical(c['local_conflicts'])!=canonical(local_conflicts) or c['minimal_families']!=minimal or len(c['candidates'])!=len(minimal):return False
            certain=all(row['certain'] for row in rows);all_ready=True;outputs=set()
            for selected,item in zip(minimal,c['candidates']):
                budget.consume()
                if set(item)!={'ports','source_scope','inventory','structural_response','crystal_paths','conclusions','resolved'}:return False
                scope=[]
                if certain:
                    for row in rows:
                        budget.consume()
                        if row['cells'][root_port]['frames'][1]==action and all(row['cells'][p]['frames'][0]==context[p] for p in selected):scope.append(row['cells'][root_port]['source'])
                    scope.sort()
                if item['ports']!=selected or item['source_scope']!=scope:return False
                literal=[];conclusions=[];resolved=False
                if scope:
                    local=decode_scope(view,scope,item['inventory'])
                    if not verify_organization_inventory(local) or not verify_channel_response(local,before,action,item['structural_response'],budget):return False
                    values={tuple(x) for x in item['structural_response']['candidates']}
                    for source in scope:
                        budget.consume();frames,receipts=view.episodes[source]
                        if decode(frames[0])!=before or decode(frames[1])!=action:continue
                        ids=frames[2];origin=receipts[2].origin;offset=len(frames[0])+len(frames[1]);occ={'frame':2,'start':0,'stop':len(ids),'event_span':[offset,offset+len(ids)],'identities':list(ids),'coordinates':[[origin[0]+p,*origin[1:]] for p in range(len(ids))]};value=decode(ids);literal.append({'source':source,'output':value,'occurrence':occ});values.add((value,))
                    conclusions=[list(value) for value in sorted(values)];resolved=item['structural_response']['status']!='INCOMPLETE' and len(conclusions)==1
                elif item['inventory'] is not None or item['structural_response'] is not None:return False
                if canonical(item['crystal_paths'])!=canonical(literal) or canonical(item['conclusions'])!=canonical(conclusions) or type(item['resolved']) is not bool or item['resolved']!=resolved:return False
                all_ready &= resolved
                if resolved:outputs.add(tuple(conclusions[0]))
            ready=certain and not local_conflicts and bool(minimal) and all_ready and len(outputs)==1
            status='MEASURED_CONTEXT_LAW_RESOLVED' if ready else 'INCOMPLETE_OBSERVATION' if not certain else 'CONTRADICTED_ORIGINAL_INPUT' if local_conflicts else 'UNRESOLVED_CONTEXT_LAWS'
            return canonical(c['result'])==canonical({'status':status,'output':list(next(iter(outputs))) if ready else []})
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

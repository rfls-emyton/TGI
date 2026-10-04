"""Independent frontier layers, prefix lineage, actual history and replan check."""
from copy import deepcopy
from .acquisition_snapshot import acquisition_snapshot
from .acquisition_witness import verify_raw_acquisition_witness
from .measured_context_layout import layout
from .organization import RawOrganization
from .identity import decode
from .frame_engine import canonical
from .role_work import RoleSearchBudget
from .joint_goal_traversal_check import verify_joint_goal_traversal,_initial_owners,_expanded_owners


def verify_joint_frontier_requests(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,goal,certificate,*,max_depth=None,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            c=deepcopy(certificate)
            if set(c)!={'policy','max_depth','search','layers','requests','result'} or c['policy']!='joint_frontier_requests_v2':return False
            if max_depth is not None and (type(max_depth) is not int or max_depth<0):return False
            if type(c['max_depth']) is not type(max_depth) or c['max_depth']!=max_depth or type(c['layers']) is not list or type(c['requests']) is not list:return False
            model,observation=acquisition_snapshot(model),acquisition_snapshot(observation);groups,measurements,observed_groups,observed_measurements,goal=deepcopy((groups,measurements,observed_groups,observed_measurements,goal));plan=c['search'];level=plan['result']['depth_reached']
            if type(level) is not int or level<0 or (max_depth is not None and level>max_depth):return False
            if not verify_joint_goal_traversal(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,goal,plan,max_depth=level):return False
            r=plan['result']
            if any(plan['nodes'][plan['edges'][index]['source']]['depth']!=level-1 for index in r['blocked_edges']):return False
            status='GOAL_READY' if r['shortest_supported_length'] is not None else 'OBSERVED_STATE_UNRESOLVED' if r['status']=='UNRESOLVED_OBSERVED_STATE' else 'FRONTIER_REQUESTS_READY' if r['blocked_edges'] else 'SUPPORTED_FRONTIER_CLOSED' if r['frontier_exhausted'] else 'DECLARED_DEPTH_REACHED' if max_depth is not None and level==max_depth else None
            if status is None:return False
            registered=[[] for _ in range(level+1)];edge_counts=[0]*(level+1)
            for index,node in enumerate(plan['nodes']):
                budget.consume();registered[node['depth']].append(index)
            for edge in plan['edges']:
                budget.consume();edge_counts[plan['nodes'][edge['source']]['depth']+1]+=1
            layers=[];nodes_stop=0;edges_stop=0
            for depth in range(level+1):
                budget.consume();nodes_stop+=len(registered[depth]);edges_stop+=edge_counts[depth]
                layers.append({'depth':depth,'registered_frontier':registered[depth],'nodes_stop':nodes_stop,'edges_stop':edges_stop})
            if canonical(c['layers'])!=canonical(layers):return False
            requests=[]
            if status=='FRONTIER_REQUESTS_READY':
                parents={i:[] for i in range(len(plan['nodes']))}
                for index,e in enumerate(plan['edges']):
                    budget.consume()
                    if e['supported'] and plan['nodes'][e['successor']]['depth']==plan['nodes'][e['source']]['depth']+1:parents[e['successor']].append(index)
                for index in plan['result']['blocked_edges']:
                    edge=plan['edges'][index];prefixes=[];pending=[(edge['source'],[])]
                    while pending:
                        budget.consume();node,back=pending.pop()
                        if node!=0:
                            for parent in reversed(parents[node]):pending.append((plan['edges'][parent]['source'],back+[parent]))
                            continue
                        path=list(reversed(back));owners=_initial_owners(plan['state_certificate'],budget);actions=[]
                        for step,j in enumerate(path):
                            budget.consume();e=plan['edges'][j];actions.append(e['action']);owners={item['port']:_expanded_owners(owners[item['port']],item['certificate'],step,e['action'],budget) for item in e['laws']}
                        prefixes.append({'edges':path,'actions':actions,'lineage_routes':owners})
                    prefixes.sort(key=lambda p:(p['actions'],p['edges']));requests.append({'edge':index,'source':edge['source'],'action':edge['action'],'before':deepcopy(plan['nodes'][edge['source']]['state']),'acquisition_distance':plan['nodes'][edge['source']]['depth']+1,'unresolved_ports':[x['port'] for x in edge['laws'] if x['certificate']['result']['status']!='MEASURED_CONTEXT_LAW_RESOLVED'],'prefixes':prefixes})
            result={'status':status,'search_depth':level,'request_count':len(requests),'minimum_acquisition_distance':min((r['acquisition_distance'] for r in requests),default=None)}
            return canonical(c['requests'])==canonical(requests) and canonical(c['result'])==canonical(result)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False


def verify_joint_frontier_update(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,goal,plan,request_index,path_index,acquired,acquired_groups,acquired_measurements,group_indices,certificate,*,max_depth=None,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            c=deepcopy(certificate);model,observation,view=acquisition_snapshot(model),acquisition_snapshot(observation),acquisition_snapshot(acquired);groups,measurements,observed_groups,observed_measurements,goal,plan,acquired_groups,acquired_measurements,group_indices=deepcopy((groups,measurements,observed_groups,observed_measurements,goal,plan,acquired_groups,acquired_measurements,group_indices))
            if set(c)!={'policy','plan','request_index','path_index','group_indices','groups','witness','steps','rebuilt_history','renewed','result'} or c['policy']!='joint_frontier_update_v3' or canonical(c['plan'])!=canonical(plan) or canonical(c['groups'])!=canonical(acquired_groups) or canonical(c['group_indices'])!=canonical(group_indices) or type(c['steps']) is not list:return False
            if not verify_joint_frontier_requests(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,goal,plan,max_depth=max_depth):return False
            if type(request_index) is not int or not 0<=request_index<len(plan['requests']) or type(c['request_index']) is not int or c['request_index']!=request_index:return False
            request=plan['requests'][request_index]
            if type(path_index) is not int or not 0<=path_index<len(request['prefixes']) or type(c['path_index']) is not int or c['path_index']!=path_index:return False
            if canonical(acquired_groups[:len(observed_groups)])!=canonical(observed_groups):return False
            lookup={(r['source'],r['frame']):r for r in acquired_measurements}
            for source,episode in observation.episodes.items():
                budget.consume()
                if source not in view.episodes or view.episodes[source]!=episode:return False
            for row in observed_measurements:
                budget.consume()
                if lookup.get((row['source'],row['frame']))!=row:return False
            prefix=request['prefixes'][path_index];prior=plan['search']['state_certificate']
            if not verify_raw_acquisition_witness(view,acquired_measurements,c['witness']):return False
            ports,rows=layout(view,acquired_groups,acquired_measurements,prior['ports'][0],budget)
            if ports!=prior['ports'] or type(group_indices) is not list or len(group_indices)!=len(prefix['actions'])+1 or any(type(i) is not int or not 0<=i<len(rows) for i in group_indices) or len(set(group_indices))!=len(group_indices):return False
            state=prior['state'];bounds={p['port']:p['measurement'] for p in prior['points']};ordered=all(row['certain'] for row in rows);steps=[];actions=[];mismatches=[];base=plan['search']
            for step,index in enumerate(group_indices):
                budget.consume();cells=rows[index]['cells'];before={p:cells[p]['frames'][0] for p in ports};after={p:cells[p]['frames'][2] for p in ports};action=cells[ports[0]]['frames'][1]
                for port in ports:
                    budget.consume();b=cells[port]['measurements'][0];old=bounds[port];ordered &= before[port]==state[port] and b['clock']==old['clock'] and old['upper']<b['lower']
                    for j,row in enumerate(rows):
                        if j==index:continue
                        budget.consume();a=row['cells'][port]['measurements'][1];ordered &= a['clock']==b['clock'] and (a['upper']<=old['upper'] or a['lower']>b['upper'])
                if step<len(prefix['edges']):
                    expected=base['nodes'][base['edges'][prefix['edges'][step]]['successor']]['state'];different=[p for p in ports if after[p]!=expected[p]]
                    if different:mismatches.append({'step':step,'ports':different})
                steps.append({'group':index,'action':action,'before':before,'after':after,'cells':deepcopy(cells)});actions.append(action);state=after;bounds={p:cells[p]['measurements'][2] for p in ports}
            if canonical(c['steps'])!=canonical(steps):return False
            matched=steps[-1]['before']==request['before'];planned=actions==prefix['actions']+[request['action']];admitted=bool(ordered and planned);status='INCOMPLETE_FRONTIER_OBSERVATION' if not ordered else 'UNPLANNED_FRONTIER_SEQUENCE' if not planned else 'UNMODELED_FRONTIER_EXECUTION' if mismatches or not matched else 'FRONTIER_EXPERIENCE_ACQUIRED';history=None;renewed_status=None
            if admitted:
                merged=RawOrganization();mapping=[];episodes=[];all_groups=[];all_measurements=[]
                for domain,original,gs,ms in [('learned',model,groups,measurements),('acquired',view,acquired_groups,acquired_measurements)]:
                    names={}
                    for ordinal,(source,(frames,_)) in enumerate(original.episodes.items()):
                        name=canonical([domain,ordinal]);budget.consume_many(sum(map(len,frames))+len(source)+len(name)+1);names[source]=name;raw=list(map(decode,frames));merged.observe(name,raw);mapping.append({'domain':domain,'ordinal':ordinal,'original_source':source,'source':name});episodes.append({'source':name,'frames':raw})
                    for group in gs:
                        budget.consume_many(len(group)+1);all_groups.append([{'port':x['port'],'source':names[x['source']]} for x in group])
                    for row in ms:
                        budget.consume();all_measurements.append({**deepcopy(row),'source':names[row['source']]})
                history={'policy':'joint_history_ordinal_v1','source_map':mapping,'episodes':episodes,'groups':all_groups,'measurements':all_measurements}
                if canonical(c['rebuilt_history'])!=canonical(history) or c['renewed'] is None:return False
                if not verify_joint_frontier_requests(merged,all_groups,all_measurements,merged,all_groups,all_measurements,len(groups)+group_indices[-1],goal,c['renewed'],max_depth=max_depth):return False
                renewed_status=c['renewed']['result']['status']
            elif c['rebuilt_history'] is not None or c['renewed'] is not None:return False
            result={'execution_status':status,'ordered':bool(ordered),'requested_actions_match':bool(planned),'frontier_before_matches':bool(matched),'prefix_mismatches':mismatches,'experience_admitted':admitted,'renewed_status':renewed_status}
            return canonical(c['result'])==canonical(result)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

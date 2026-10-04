"""First unresolved joint frontier, original actual acquisition and renewed laws."""
from copy import deepcopy
from .acquisition_snapshot import acquisition_snapshot
from .acquisition_witness import certify_raw_acquisition_witness
from .measured_context_layout import layout
from .organization import RawOrganization
from .identity import decode
from .frame_engine import canonical
from .role_work import RoleSearchBudget
from .joint_goal_traversal import _certify_goal_graph,_seed_routes,_next_routes


def _terminal(plan,level,max_depth):
    result=plan['result']
    if result['shortest_supported_length'] is not None:return 'GOAL_READY'
    if result['status']=='UNRESOLVED_OBSERVED_STATE':return 'OBSERVED_STATE_UNRESOLVED'
    if result['blocked_edges']:return 'FRONTIER_REQUESTS_READY'
    if result['frontier_exhausted']:return 'SUPPORTED_FRONTIER_CLOSED'
    if max_depth is not None and level==max_depth:return 'DECLARED_DEPTH_REACHED'
    return None


def _requests(plan,budget):
    parents={i:[] for i in range(len(plan['nodes']))}
    for i,e in enumerate(plan['edges']):
        budget.consume()
        if e['supported'] and plan['nodes'][e['successor']]['depth']==plan['nodes'][e['source']]['depth']+1:parents[e['successor']].append(i)
    requests=[]
    for index in plan['result']['blocked_edges']:
        edge=plan['edges'][index];paths=[];stack=[(edge['source'],[])]
        while stack:
            budget.consume();node,reverse=stack.pop()
            if node:
                for parent in reversed(parents[node]):stack.append((plan['edges'][parent]['source'],reverse+[parent]))
                continue
            path=list(reversed(reverse));owners=_seed_routes(plan['state_certificate'],budget);actions=[]
            for step,j in enumerate(path):
                budget.consume();e=plan['edges'][j];actions.append(e['action']);owners={item['port']:_next_routes(owners[item['port']],item['certificate'],step,e['action'],budget) for item in e['laws']}
            paths.append({'edges':path,'actions':actions,'lineage_routes':owners})
        paths.sort(key=lambda p:(p['actions'],p['edges']));requests.append({'edge':index,'source':edge['source'],'action':edge['action'],'before':deepcopy(plan['nodes'][edge['source']]['state']),'acquisition_distance':plan['nodes'][edge['source']]['depth']+1,'unresolved_ports':[x['port'] for x in edge['laws'] if x['certificate']['result']['status']!='MEASURED_CONTEXT_LAW_RESOLVED'],'prefixes':paths})
    return requests


def certify_joint_frontier_requests(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,goal,*,max_depth=None,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        if max_depth is not None and (type(max_depth) is not int or max_depth<0):raise ValueError('Depth is None or nonnegative exact integer')
        model,observation=acquisition_snapshot(model),acquisition_snapshot(observation);groups,measurements,observed_groups,observed_measurements,goal=deepcopy((groups,measurements,observed_groups,observed_measurements,goal))
        plan=_certify_goal_graph(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,goal,max_depth=max_depth,stop_at_first_blocked=True)
        level=plan['result']['depth_reached'];status=_terminal(plan,level,max_depth)
        if status is None:raise ValueError('Frontier graph has no stopping event')
        registered=[[] for _ in range(level+1)];edge_counts=[0]*(level+1)
        for index,node in enumerate(plan['nodes']):
            budget.consume();registered[node['depth']].append(index)
        for edge in plan['edges']:
            budget.consume();edge_counts[plan['nodes'][edge['source']]['depth']+1]+=1
        layers=[];nodes_stop=0;edges_stop=0
        for depth in range(level+1):
            budget.consume();nodes_stop+=len(registered[depth]);edges_stop+=edge_counts[depth]
            layers.append({'depth':depth,'registered_frontier':registered[depth],'nodes_stop':nodes_stop,'edges_stop':edges_stop})
        requests=_requests(plan,budget) if status=='FRONTIER_REQUESTS_READY' else []
        return {'policy':'joint_frontier_requests_v2','max_depth':max_depth,'search':plan,'layers':layers,'requests':requests,'result':{'status':status,'search_depth':level,'request_count':len(requests),'minimum_acquisition_distance':min((r['acquisition_distance'] for r in requests),default=None)}}


def _rebuild(model,groups,measurements,acquired,acquired_groups,acquired_measurements,budget):
    combined=RawOrganization();mapping=[];episodes=[];all_groups=[];all_measurements=[]
    for domain,view,gs,ms in [('learned',model,groups,measurements),('acquired',acquired,acquired_groups,acquired_measurements)]:
        names={}
        for ordinal,(source,(frames,_)) in enumerate(view.episodes.items()):
            name=canonical([domain,ordinal]);budget.consume_many(sum(map(len,frames))+len(source)+len(name)+1);names[source]=name;raw=list(map(decode,frames));combined.observe(name,raw);mapping.append({'domain':domain,'ordinal':ordinal,'original_source':source,'source':name});episodes.append({'source':name,'frames':raw})
        for group in gs:
            budget.consume_many(len(group)+1);all_groups.append([{'port':x['port'],'source':names[x['source']]} for x in group])
        for row in ms:
            budget.consume();all_measurements.append({**deepcopy(row),'source':names[row['source']]})
    return combined,{'policy':'joint_history_ordinal_v1','source_map':mapping,'episodes':episodes,'groups':all_groups,'measurements':all_measurements}


def certify_joint_frontier_update(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,goal,plan,request_index,path_index,acquired,acquired_groups,acquired_measurements,group_indices,*,max_depth=None,max_search_steps=None):
    from .joint_frontier_acquisition_check import verify_joint_frontier_requests
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume();model,observation,view=acquisition_snapshot(model),acquisition_snapshot(observation),acquisition_snapshot(acquired);groups,measurements,observed_groups,observed_measurements,goal,plan,acquired_groups,acquired_measurements,group_indices=deepcopy((groups,measurements,observed_groups,observed_measurements,goal,plan,acquired_groups,acquired_measurements,group_indices))
        if not verify_joint_frontier_requests(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,goal,plan,max_depth=max_depth):raise ValueError('Invalid or stale frontier request')
        if type(request_index) is not int or not 0<=request_index<len(plan['requests']):raise ValueError('Original request index required')
        request=plan['requests'][request_index]
        if type(path_index) is not int or not 0<=path_index<len(request['prefixes']):raise ValueError('Original shortest prefix index required')
        if canonical(acquired_groups[:len(observed_groups)])!=canonical(observed_groups):raise ValueError('Original observation group prefix must be retained')
        lookup={(r['source'],r['frame']):r for r in acquired_measurements}
        for source,episode in observation.episodes.items():
            budget.consume()
            if source not in view.episodes or view.episodes[source]!=episode:raise ValueError('Original observed episode prefix must be retained')
        for row in observed_measurements:
            budget.consume()
            if lookup.get((row['source'],row['frame']))!=row:raise ValueError('Original observed measurements must be retained')
        prefix=request['prefixes'][path_index];prior=plan['search']['state_certificate'];witness=certify_raw_acquisition_witness(view,acquired_measurements);ports,rows=layout(view,acquired_groups,acquired_measurements,prior['ports'][0],budget)
        if ports!=prior['ports'] or type(group_indices) is not list or len(group_indices)!=len(prefix['actions'])+1 or any(type(i) is not int or not 0<=i<len(rows) for i in group_indices) or len(set(group_indices))!=len(group_indices):raise ValueError('Complete ordered unique prefix/frontier groups required')
        previous=prior['state'];bounds={p['port']:p['measurement'] for p in prior['points']};ordered=all(r['certain'] for r in rows);steps=[];actions=[];mismatches=[];base=plan['search']
        for step,index in enumerate(group_indices):
            budget.consume();cells=rows[index]['cells'];before={p:cells[p]['frames'][0] for p in ports};after={p:cells[p]['frames'][2] for p in ports};action=cells[ports[0]]['frames'][1]
            for port in ports:
                budget.consume();b=cells[port]['measurements'][0];old=bounds[port];ordered &= before[port]==previous[port] and b['clock']==old['clock'] and old['upper']<b['lower']
                for other,row in enumerate(rows):
                    if other==index:continue
                    budget.consume();a=row['cells'][port]['measurements'][1];ordered &= a['clock']==b['clock'] and (a['upper']<=old['upper'] or a['lower']>b['upper'])
            if step<len(prefix['edges']):
                expected=base['nodes'][base['edges'][prefix['edges'][step]]['successor']]['state'];different=[p for p in ports if after[p]!=expected[p]]
                if different:mismatches.append({'step':step,'ports':different})
            steps.append({'group':index,'action':action,'before':before,'after':after,'cells':deepcopy(cells)});actions.append(action);previous=after;bounds={p:cells[p]['measurements'][2] for p in ports}
        before_matches=steps[-1]['before']==request['before'];planned=actions==prefix['actions']+[request['action']];admitted=bool(ordered and planned);status='INCOMPLETE_FRONTIER_OBSERVATION' if not ordered else 'UNPLANNED_FRONTIER_SEQUENCE' if not planned else 'UNMODELED_FRONTIER_EXECUTION' if mismatches or not before_matches else 'FRONTIER_EXPERIENCE_ACQUIRED';history=None;renewed=None
        if admitted:
            merged,history=_rebuild(model,groups,measurements,view,acquired_groups,acquired_measurements,budget);anchor=len(groups)+group_indices[-1];renewed=certify_joint_frontier_requests(merged,history['groups'],history['measurements'],merged,history['groups'],history['measurements'],anchor,goal,max_depth=max_depth)
        result={'execution_status':status,'ordered':bool(ordered),'requested_actions_match':bool(planned),'frontier_before_matches':bool(before_matches),'prefix_mismatches':mismatches,'experience_admitted':admitted,'renewed_status':None if renewed is None else renewed['result']['status']}
        return {'policy':'joint_frontier_update_v3','plan':plan,'request_index':request_index,'path_index':path_index,'group_indices':group_indices,'groups':acquired_groups,'witness':witness,'steps':steps,'rebuilt_history':history,'renewed':renewed,'result':result}

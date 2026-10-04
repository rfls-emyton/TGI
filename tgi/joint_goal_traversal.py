"""Complete shortest supported joint-state paths and expanded NMU lineage."""
from copy import deepcopy
from .identity import encode
from .acquisition_snapshot import acquisition_snapshot
from .frame_engine import canonical
from .observed_joint_state import certify_observed_joint_state
from .measured_context_laws import certify_measured_context_laws
from .role_work import RoleSearchBudget


def _seed_routes(state,budget):
    result={}
    for point in state['points']:
        p=point['port'];occ=point['occurrence'];route=[]
        for i,coord in enumerate(occ['coordinates']):
            budget.consume();route.append({'kind':'observed','domain':'observed','port':p,'source':point['source'],'frame':occ['frame'],'position':i,'coordinate':deepcopy(coord)})
        result[p]=[route]
    return result


def _next_routes(previous,law,step,action,budget):
    routes={};port=law['root_port']
    for candidate in law['candidates']:
        for proof in candidate['structural_response']['proofs']:
            if proof['output']!=law['result']['output']:continue
            for prior in previous:
                route=[]
                for point in proof['characters'][0]:
                    budget.consume()
                    if point['kind']=='trigger':
                        if point['frame']==0:route.append(deepcopy(prior[point['position']]))
                        else:route.append({'kind':'action','domain':'query_action','step':step,'action':action,'position':point['position']})
                    else:route.append({**deepcopy(point),'domain':'learned','port':port})
                routes[canonical(route)]=route
        for witness in candidate['crystal_paths']:
            route=[]
            for i,coord in enumerate(witness['occurrence']['coordinates']):
                budget.consume();route.append({'kind':'crystal','domain':'learned','port':port,'source':witness['source'],'frame':2,'position':i,'coordinate':deepcopy(coord)})
            routes[canonical(route)]=route
    if not routes:raise ValueError('Resolved law lacks a complete character route')
    return [routes[key] for key in sorted(routes)]


def _certify_goal_graph(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,goal,*,max_depth=None,max_search_steps=None,stop_at_first_blocked=False):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        if max_depth is not None and (type(max_depth) is not int or max_depth<0):raise ValueError('Depth is None or a nonnegative integer')
        model,observation=acquisition_snapshot(model),acquisition_snapshot(observation)
        groups,measurements,observed_groups,observed_measurements=deepcopy((groups,measurements,observed_groups,observed_measurements))
        state=certify_observed_joint_state(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group);goal=deepcopy(goal)
        if not isinstance(goal,dict) or not goal or not set(goal)<=set(state['ports']):raise ValueError('Nonempty original-interface goal required')
        for value in goal.values():
            if not isinstance(value,str) or not value:raise ValueError('Nonempty raw goal frames required')
            encode(value)
        ready=state['result']['status']=='JOINT_STATE_READY';nodes=[{'state':deepcopy(state['state']),'depth':0,'kind':'OBSERVED_SCOPE_VALUES'}];known={canonical(state['state']):0};edges=[];predecessors={0:[]};frontier=[0] if ready else [];depth=0;blocked=[];goals=[0] if ready and all(state['state'][p]==v for p,v in goal.items()) else [];found=0 if goals else None
        while frontier and found is None and (max_depth is None or depth<max_depth):
            upcoming=[]
            for source in frontier:
                before=nodes[source]['state']
                for action in state['inventory']:
                    budget.consume();laws=[];after={};supported=True
                    for port in state['ports']:
                        budget.consume();context={p:before[p] for p in state['ports'] if p!=port};law=certify_measured_context_laws(model,groups,measurements,port,before[port],action,context);laws.append({'port':port,'certificate':law})
                        if law['result']['status']=='MEASURED_CONTEXT_LAW_RESOLVED':after[port]=law['result']['output'][0]
                        else:supported=False
                    successor=None;index=len(edges)
                    if supported:
                        key=canonical(after)
                        if key not in known:
                            successor=len(nodes);known[key]=successor;nodes.append({'state':after,'depth':depth+1,'kind':'PROJECTED'});predecessors[successor]=[];upcoming.append(successor)
                        else:successor=known[key]
                        if nodes[successor]['depth']==depth+1:predecessors[successor].append(index)
                        if all(after[p]==v for p,v in goal.items()):
                            found=depth+1 if found is None else found
                            if successor not in goals:goals.append(successor)
                    else:blocked.append(index)
                    edges.append({'source':source,'action':action,'laws':laws,'successor':successor,'supported':bool(supported)})
            frontier=upcoming;depth+=1
            if stop_at_first_blocked and blocked:break
        solutions=[]
        for target in sorted(goals):
            pending=[(target,[])]
            while pending:
                budget.consume();node,reverse=pending.pop()
                if node:
                    for edge in reversed(predecessors[node]):pending.append((edges[edge]['source'],reverse+[edge]))
                    continue
                path=list(reversed(reverse));owners=_seed_routes(state,budget);actions=[]
                for step,edge_index in enumerate(path):
                    budget.consume();edge=edges[edge_index];actions.append(edge['action']);next_owners={}
                    for item in edge['laws']:next_owners[item['port']]=_next_routes(owners[item['port']],item['certificate'],step,edge['action'],budget)
                    owners=next_owners
                solutions.append({'goal_node':target,'edges':path,'actions':actions,'lineage_routes':owners})
        solutions.sort(key=lambda s:(s['actions'],s['edges']));status='UNRESOLVED_OBSERVED_STATE' if not ready else 'GOAL_ALREADY_OBSERVED' if found==0 else 'SUPPORTED_GOAL_PATH_FOUND' if found is not None else 'UNRESOLVED_GOAL_FRONTIER' if blocked else 'NO_SUPPORTED_GOAL_PATH_WITHIN_DEPTH' if frontier else 'NO_SUPPORTED_GOAL_PATH'
        result={'status':status,'shortest_supported_length':found,'paths':[s['actions'] for s in solutions],'goal_nodes':sorted(goals),'blocked_edges':blocked,'frontier':frontier,'depth_reached':depth,'frontier_exhausted':not bool(frontier)}
        return {'policy':'joint_goal_traversal_v1','goal':goal,'max_depth':depth if stop_at_first_blocked else max_depth,'state_certificate':state,'nodes':nodes,'edges':edges,'solutions':solutions,'result':result}


def certify_joint_goal_traversal(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,goal,*,max_depth=None,max_search_steps=None):
    return _certify_goal_graph(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,goal,max_depth=max_depth,max_search_steps=max_search_steps)

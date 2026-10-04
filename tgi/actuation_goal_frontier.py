"""Complete shortest supported joint-state paths and expanded NMU lineage."""
from copy import deepcopy
from .identity import encode
from .acquisition_snapshot import acquisition_snapshot
from .frame_engine import canonical
from .observed_actuation_discovery import certify_observed_actuation_discovery
from .joint_frontier_acquisition import _requests
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


def certify_actuation_goal_frontier(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,catalogue,catalogue_measurements,goal,*,max_depth=None,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        if max_depth is not None and (type(max_depth) is not int or max_depth<0):raise ValueError('Depth is None or a nonnegative integer')
        model,observation=acquisition_snapshot(model),acquisition_snapshot(observation)
        groups,measurements,observed_groups,observed_measurements=deepcopy((groups,measurements,observed_groups,observed_measurements))
        discovery=certify_observed_actuation_discovery(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,catalogue,catalogue_measurements);state=discovery['state_certificate'];goal=deepcopy(goal)
        if not isinstance(goal,dict) or not goal or not set(goal)<=set(state['ports']):raise ValueError('Nonempty original-interface goal required')
        for value in goal.values():
            if not isinstance(value,str) or not value:raise ValueError('Nonempty raw goal frames required')
            encode(value)
        ready=state['result']['status']=='JOINT_STATE_READY';nodes=[{'state':deepcopy(state['state']),'depth':0,'kind':'OBSERVED_SCOPE_VALUES'}];known={canonical(state['state']):0};edges=[];predecessors={0:[]};frontier=[0] if ready and discovery['result']['catalogue_current'] else [];depth=0;blocked=[];goals=[0] if ready and all(state['state'][p]==v for p,v in goal.items()) else [];found=0 if goals else None
        while frontier and found is None and (max_depth is None or depth<max_depth):
            upcoming=[]
            for source in frontier:
                before=nodes[source]['state']
                for action in discovery['available_actions']:
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
            if blocked:break
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
        solutions.sort(key=lambda s:(s['actions'],s['edges']))
        graph={'state_certificate':state,'nodes':nodes,'edges':edges,'result':{'blocked_edges':blocked}}
        requests=_requests(graph,budget);choices=[]
        for solution in solutions:choices.append({'kind':'SUPPORTED_GOAL','target':solution['goal_node'],**deepcopy(solution)})
        for request in requests:
            for prefix in request['prefixes']:choices.append({'kind':'FRONTIER_EXPERIENCE','target':request['edge'],'edges':prefix['edges']+[request['edge']],'actions':prefix['actions']+[request['action']],'lineage_routes':deepcopy(prefix['lineage_routes'])})
        for target in frontier:
            if target in goals:continue
            paths=[(target,[])]
            while paths:
                budget.consume();node,reverse=paths.pop()
                if node:
                    for edge_index in reversed(predecessors[node]):paths.append((edges[edge_index]['source'],reverse+[edge_index]))
                    continue
                path=list(reversed(reverse));owners=_seed_routes(state,budget);actions=[]
                for step,j in enumerate(path):
                    budget.consume();edge=edges[j];actions.append(edge['action']);owners={item['port']:_next_routes(owners[item['port']],item['certificate'],step,edge['action'],budget) for item in edge['laws']}
                choices.append({'kind':'SUPPORTED_PREFIX','target':target,'edges':path,'actions':actions,'lineage_routes':owners})
        choices.sort(key=lambda x:(x['kind'],x['target'],x['actions'],x['edges']))
        status='GOAL_ALREADY_OBSERVED' if found==0 else 'OBSERVED_STATE_UNRESOLVED' if not ready else 'CATALOGUE_NOT_CURRENT' if not discovery['result']['catalogue_current'] else 'SUPPORTED_GOAL_READY' if found is not None else 'FRONTIER_EXPERIENCE_READY' if blocked else 'SUPPORTED_FRONTIER_CLOSED' if not frontier else 'DECLARED_DEPTH_REACHED'
        result={'status':status,'shortest_supported_goal_length':found,'goal_nodes':sorted(goals),'blocked_edges':blocked,'frontier':frontier,'depth_reached':depth,'supported_frontier_exhausted':not bool(frontier),'choice_count':len(choices),'request_count':len(requests),'minimum_acquisition_distance':min((r['acquisition_distance'] for r in requests),default=None),'catalogue_current':discovery['result']['catalogue_current']}
        return {'policy':'actuation_goal_frontier_v1','goal':goal,'max_depth':max_depth,'discovery':discovery,'state_certificate':state,'nodes':nodes,'edges':edges,'solutions':solutions,'requests':requests,'choices':choices,'result':result}

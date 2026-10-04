"""Independent graph coverage, goal paths and correlated character-route check."""
from copy import deepcopy
from .identity import encode
from .acquisition_snapshot import acquisition_snapshot
from .frame_engine import canonical
from .observed_actuation_discovery_check import verify_observed_actuation_discovery
from .measured_context_laws_check import verify_measured_context_laws
from .role_work import RoleSearchBudget


def _initial_owners(state,budget):
    owners={}
    for point in state['points']:
        route=[];occ=point['occurrence']
        for i,coordinate in enumerate(occ['coordinates']):
            budget.consume();route.append({'kind':'observed','domain':'observed','port':point['port'],'source':point['source'],'frame':occ['frame'],'position':i,'coordinate':deepcopy(coordinate)})
        owners[point['port']]=[route]
    return owners


def _expanded_owners(priors,law,step,action,budget):
    distinct={};port=law['root_port']
    for family in law['candidates']:
        for proof in family['structural_response']['proofs']:
            if proof['output']!=law['result']['output']:continue
            for prior in priors:
                current=[]
                for point in proof['characters'][0]:
                    budget.consume()
                    if point['kind']=='crystal':current.append({**deepcopy(point),'domain':'learned','port':port})
                    elif point['frame']==0:current.append(deepcopy(prior[point['position']]))
                    elif point['frame']==1:current.append({'kind':'action','domain':'query_action','step':step,'action':action,'position':point['position']})
                    else:raise ValueError('Invalid original trigger frame')
                distinct[canonical(current)]=current
        for crystal in family['crystal_paths']:
            current=[]
            for position,coordinate in enumerate(crystal['occurrence']['coordinates']):
                budget.consume();current.append({'kind':'crystal','domain':'learned','port':port,'source':crystal['source'],'frame':2,'position':position,'coordinate':deepcopy(coordinate)})
            distinct[canonical(current)]=current
    if not distinct:raise ValueError('Missing lineage route')
    return [distinct[k] for k in sorted(distinct)]


def verify_actuation_goal_frontier(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,catalogue,catalogue_measurements,goal,certificate,*,max_depth=None,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            c=deepcopy(certificate)
            if set(c)!={'policy','goal','max_depth','discovery','state_certificate','nodes','edges','solutions','requests','choices','result'} or c['policy']!='actuation_goal_frontier_v1':return False
            if max_depth is not None and (type(max_depth) is not int or max_depth<0):return False
            if canonical(c['goal'])!=canonical(goal) or type(c['max_depth']) is not type(max_depth) or c['max_depth']!=max_depth:return False
            if any(type(c[key]) is not list for key in ('nodes','edges','solutions')):return False
            model,observation=acquisition_snapshot(model),acquisition_snapshot(observation)
            groups,measurements,observed_groups,observed_measurements=deepcopy((groups,measurements,observed_groups,observed_measurements))
            state=c['state_certificate']
            discovery=c['discovery']
            if not verify_observed_actuation_discovery(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,catalogue,catalogue_measurements,discovery) or canonical(state)!=canonical(discovery['state_certificate']):return False
            if not isinstance(goal,dict) or not goal or not set(goal)<=set(state['ports']):return False
            for value in goal.values():
                if not isinstance(value,str) or not value:return False
                encode(value)
            ready=state['result']['status']=='JOINT_STATE_READY';expected_nodes=[{'state':deepcopy(state['state']),'depth':0,'kind':'OBSERVED_SCOPE_VALUES'}];registered={canonical(state['state']):0};parents={0:[]};layer=[0] if ready and discovery['result']['catalogue_current'] else [];level=0;cursor=0;blocked=[];goals=[0] if ready and all(state['state'][p]==v for p,v in goal.items()) else [];found=0 if goals else None
            while layer and found is None and (max_depth is None or level<max_depth):
                following=[]
                for source in layer:
                    before=expected_nodes[source]['state']
                    for action in discovery['available_actions']:
                        budget.consume()
                        if cursor>=len(c['edges']):return False
                        edge=c['edges'][cursor]
                        if set(edge)!={'source','action','laws','successor','supported'} or type(edge['source']) is not int or edge['source']!=source or edge['action']!=action or len(edge['laws'])!=len(state['ports']):return False
                        after={};supported=True
                        for port,item in zip(state['ports'],edge['laws']):
                            budget.consume()
                            if set(item)!={'port','certificate'} or item['port']!=port:return False
                            context={p:before[p] for p in state['ports'] if p!=port};law=item['certificate']
                            if not verify_measured_context_laws(model,groups,measurements,port,before[port],action,context,law):return False
                            if law['result']['status']=='MEASURED_CONTEXT_LAW_RESOLVED':after[port]=law['result']['output'][0]
                            else:supported=False
                        successor=None
                        if supported:
                            key=canonical(after)
                            if key in registered:successor=registered[key]
                            else:
                                successor=len(expected_nodes);registered[key]=successor;expected_nodes.append({'state':after,'depth':level+1,'kind':'PROJECTED'});parents[successor]=[];following.append(successor)
                            if expected_nodes[successor]['depth']==level+1:parents[successor].append(cursor)
                            if all(after[p]==v for p,v in goal.items()):
                                found=level+1 if found is None else found
                                if successor not in goals:goals.append(successor)
                        else:blocked.append(cursor)
                        if type(edge['supported']) is not bool or edge['supported']!=supported or (successor is not None and type(edge['successor']) is not int) or edge['successor']!=successor:return False
                        cursor+=1
                layer=following;level+=1
                if blocked:break
            if len(c['edges'])!=cursor or canonical(c['nodes'])!=canonical(expected_nodes):return False
            expected_solutions=[]
            for target in sorted(goals):
                stack=[(target,[])]
                while stack:
                    budget.consume();node,reverse=stack.pop()
                    if node!=0:
                        for edge_index in reversed(parents[node]):stack.append((c['edges'][edge_index]['source'],reverse+[edge_index]))
                        continue
                    path=list(reversed(reverse));owners=_initial_owners(state,budget);actions=[]
                    for step,edge_index in enumerate(path):
                        budget.consume();edge=c['edges'][edge_index];actions.append(edge['action']);updated={}
                        for item in edge['laws']:updated[item['port']]=_expanded_owners(owners[item['port']],item['certificate'],step,edge['action'],budget)
                        owners=updated
                    expected_solutions.append({'goal_node':target,'edges':path,'actions':actions,'lineage_routes':owners})
            expected_solutions.sort(key=lambda s:(s['actions'],s['edges']))
            if canonical(c['solutions'])!=canonical(expected_solutions):return False
            requests=[]
            for index in blocked:
                edge=c['edges'][index];paths=[];stack=[(edge['source'],[])]
                while stack:
                    budget.consume();node,reverse=stack.pop()
                    if node:
                        for parent in reversed(parents[node]):stack.append((c['edges'][parent]['source'],reverse+[parent]))
                        continue
                    path=list(reversed(reverse));owners=_initial_owners(state,budget);actions=[]
                    for step,j in enumerate(path):
                        budget.consume();e=c['edges'][j];actions.append(e['action']);owners={item['port']:_expanded_owners(owners[item['port']],item['certificate'],step,e['action'],budget) for item in e['laws']}
                    paths.append({'edges':path,'actions':actions,'lineage_routes':owners})
                paths.sort(key=lambda p:(p['actions'],p['edges']));requests.append({'edge':index,'source':edge['source'],'action':edge['action'],'before':deepcopy(expected_nodes[edge['source']]['state']),'acquisition_distance':expected_nodes[edge['source']]['depth']+1,'unresolved_ports':[item['port'] for item in edge['laws'] if item['certificate']['result']['status']!='MEASURED_CONTEXT_LAW_RESOLVED'],'prefixes':paths})
            choices=[]
            for solution in expected_solutions:choices.append({'kind':'SUPPORTED_GOAL','target':solution['goal_node'],**deepcopy(solution)})
            for request in requests:
                for prefix in request['prefixes']:choices.append({'kind':'FRONTIER_EXPERIENCE','target':request['edge'],'edges':prefix['edges']+[request['edge']],'actions':prefix['actions']+[request['action']],'lineage_routes':deepcopy(prefix['lineage_routes'])})
            for target in layer:
                if target in goals:continue
                pending=[(target,[])]
                while pending:
                    budget.consume();node,reverse=pending.pop()
                    if node:
                        for parent in reversed(parents[node]):pending.append((c['edges'][parent]['source'],reverse+[parent]))
                        continue
                    path=list(reversed(reverse));owners=_initial_owners(state,budget);actions=[]
                    for step,j in enumerate(path):
                        budget.consume();edge=c['edges'][j];actions.append(edge['action']);owners={item['port']:_expanded_owners(owners[item['port']],item['certificate'],step,edge['action'],budget) for item in edge['laws']}
                    choices.append({'kind':'SUPPORTED_PREFIX','target':target,'edges':path,'actions':actions,'lineage_routes':owners})
            choices.sort(key=lambda x:(x['kind'],x['target'],x['actions'],x['edges']))
            if canonical(c['requests'])!=canonical(requests) or canonical(c['choices'])!=canonical(choices):return False
            status='GOAL_ALREADY_OBSERVED' if found==0 else 'OBSERVED_STATE_UNRESOLVED' if not ready else 'CATALOGUE_NOT_CURRENT' if not discovery['result']['catalogue_current'] else 'SUPPORTED_GOAL_READY' if found is not None else 'FRONTIER_EXPERIENCE_READY' if blocked else 'SUPPORTED_FRONTIER_CLOSED' if not layer else 'DECLARED_DEPTH_REACHED'
            result={'status':status,'shortest_supported_goal_length':found,'goal_nodes':sorted(goals),'blocked_edges':blocked,'frontier':layer,'depth_reached':level,'supported_frontier_exhausted':not bool(layer),'choice_count':len(choices),'request_count':len(requests),'minimum_acquisition_distance':min((r['acquisition_distance'] for r in requests),default=None),'catalogue_current':discovery['result']['catalogue_current']}
            return canonical(c['result'])==canonical(result)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

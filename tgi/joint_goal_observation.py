"""Bind a planned joint path to every actual intermediate acquired state."""
from copy import deepcopy
from .acquisition_snapshot import acquisition_snapshot
from .acquisition_witness import certify_raw_acquisition_witness
from .measured_context_layout import layout
from .frame_engine import canonical
from .joint_goal_traversal_check import verify_joint_goal_traversal
from .role_work import RoleSearchBudget


def certify_joint_goal_observation(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,goal,plan,acquired,acquired_groups,acquired_measurements,group_indices,*,max_depth=None,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume();model,observation,view=acquisition_snapshot(model),acquisition_snapshot(observation),acquisition_snapshot(acquired)
        groups,measurements,observed_groups,observed_measurements,goal,plan,acquired_groups,acquired_measurements,group_indices=deepcopy((groups,measurements,observed_groups,observed_measurements,goal,plan,acquired_groups,acquired_measurements,group_indices))
        if not verify_joint_goal_traversal(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,goal,plan,max_depth=max_depth):raise ValueError('Invalid or stale goal plan')
        witness=certify_raw_acquisition_witness(view,acquired_measurements);prior=plan['state_certificate'];ports,rows=layout(view,acquired_groups,acquired_measurements,prior['ports'][0],budget)
        if ports!=prior['ports'] or not isinstance(group_indices,(list,tuple)) or not group_indices or any(type(i) is not int or not 0<=i<len(rows) for i in group_indices) or len(set(group_indices))!=len(group_indices):raise ValueError('Ordered unique original acquired groups required')
        previous=prior['state'];bounds={p['port']:p['measurement'] for p in prior['points']};ordered=all(r['certain'] for r in rows);steps=[];actions=[];actual=[]
        for index in group_indices:
            budget.consume();cells=rows[index]['cells'];before={p:cells[p]['frames'][0] for p in ports};after={p:cells[p]['frames'][2] for p in ports};action=cells[ports[0]]['frames'][1]
            for port in ports:
                budget.consume();b=cells[port]['measurements'][0];old=bounds[port];ordered &= before[port]==previous[port] and b['clock']==old['clock'] and old['upper']<b['lower']
                for other,row in enumerate(rows):
                    if other==index:continue
                    budget.consume();a=row['cells'][port]['measurements'][1];ordered &= a['clock']==b['clock'] and (a['upper']<=old['upper'] or a['lower']>b['upper'])
            steps.append({'group':index,'action':action,'before':before,'after':after,'cells':deepcopy(cells)});actions.append(action);actual.append(after);previous=after;bounds={p:cells[p]['measurements'][2] for p in ports}
        matched=[i for i,s in enumerate(plan['solutions']) if s['actions'][:len(actions)]==actions];expected=[];mismatches=[]
        if matched:
            for edge in plan['solutions'][matched[0]]['edges'][:len(actions)]:expected.append(deepcopy(plan['nodes'][plan['edges'][edge]['successor']]['state']))
            for step,(wanted,got) in enumerate(zip(expected,actual)):
                different=[p for p in ports if wanted[p]!=got[p]]
                if different:mismatches.append({'step':step,'ports':different})
        goal_matches=all(actual[-1][p]==v for p,v in goal.items());full=bool(matched) and len(actions)==len(plan['solutions'][matched[0]]['actions']);status='INCOMPLETE_GOAL_OBSERVATION';confirmed={}
        if ordered:status='UNPLANNED_GOAL_SEQUENCE' if not matched else 'UNMODELED_GOAL_RESPONSE' if mismatches else 'GOAL_RESPONSE_CONFIRMED' if full and goal_matches else 'GOAL_PATH_PREFIX_CONFIRMED'
        if status=='GOAL_RESPONSE_CONFIRMED':
            for port,routes in plan['solutions'][matched[0]]['lineage_routes'].items():
                expanded=[]
                for route in routes:
                    actual_route=[]
                    for owner in route:
                        budget.consume()
                        if owner['kind']=='action':
                            step=owner['step'];cell=steps[step]['cells'][port];position=owner['position'];actual_route.append({'kind':'acquired_action','domain':'acquired','step':step,'port':port,'source':cell['source'],'frame':1,'position':position,'coordinate':deepcopy(cell['occurrences'][1]['coordinates'][position])})
                        else:actual_route.append(deepcopy(owner))
                    expanded.append(actual_route)
                confirmed[port]=expanded
        result={'status':status,'ordered':bool(ordered),'matched_solutions':matched,'expected_trace':expected,'actual_trace':actual,'mismatches':mismatches,'goal_matches':bool(goal_matches),'confirmed_lineage_routes':confirmed}
        return {'policy':'joint_goal_observation_v1','plan':plan,'groups':acquired_groups,'group_indices':list(group_indices),'witness':witness,'steps':steps,'result':result}

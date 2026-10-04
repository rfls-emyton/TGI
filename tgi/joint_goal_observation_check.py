"""Independent actual ordered path and intermediate-state goal verifier."""
from copy import deepcopy
from .acquisition_snapshot import acquisition_snapshot
from .acquisition_witness import verify_raw_acquisition_witness
from .measured_context_layout import layout
from .frame_engine import canonical
from .joint_goal_traversal_check import verify_joint_goal_traversal
from .role_work import RoleSearchBudget


def verify_joint_goal_observation(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,goal,plan,acquired,acquired_groups,acquired_measurements,group_indices,certificate,*,max_depth=None,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            c=deepcopy(certificate);model,observation,view=acquisition_snapshot(model),acquisition_snapshot(observation),acquisition_snapshot(acquired)
            groups,measurements,observed_groups,observed_measurements,goal,plan,acquired_groups,acquired_measurements,group_indices=deepcopy((groups,measurements,observed_groups,observed_measurements,goal,plan,acquired_groups,acquired_measurements,group_indices))
            if set(c)!={'policy','plan','groups','group_indices','witness','steps','result'} or c['policy']!='joint_goal_observation_v1' or canonical(c['plan'])!=canonical(plan) or canonical(c['groups'])!=canonical(acquired_groups):return False
            if not verify_joint_goal_traversal(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,goal,plan,max_depth=max_depth):return False
            if not verify_raw_acquisition_witness(view,acquired_measurements,c['witness']):return False
            prior=plan['state_certificate'];ports,rows=layout(view,acquired_groups,acquired_measurements,prior['ports'][0],budget)
            if ports!=prior['ports'] or not isinstance(group_indices,(list,tuple)) or not group_indices or any(type(i) is not int or not 0<=i<len(rows) for i in group_indices) or len(set(group_indices))!=len(group_indices) or canonical(c['group_indices'])!=canonical(list(group_indices)) or type(c['steps']) is not list:return False
            previous=dict(prior['state']);points={p['port']:p['measurement'] for p in prior['points']};ordered=all(row['certain'] for row in rows);steps=[];actions=[];actual=[]
            for index in group_indices:
                budget.consume();cells=rows[index]['cells'];before={p:cells[p]['frames'][0] for p in ports};after={p:cells[p]['frames'][2] for p in ports};action=cells[ports[0]]['frames'][1]
                for port in ports:
                    budget.consume();b=cells[port]['measurements'][0];previous_point=points[port];ordered &= before[port]==previous[port] and b['clock']==previous_point['clock'] and b['lower']>previous_point['upper']
                    for i,row in enumerate(rows):
                        if i==index:continue
                        budget.consume();interval=row['cells'][port]['measurements'][1];ordered &= interval['clock']==b['clock'] and (interval['upper']<=previous_point['upper'] or interval['lower']>b['upper'])
                steps.append({'group':index,'action':action,'before':before,'after':after,'cells':deepcopy(cells)});actions.append(action);actual.append(after);previous=after;points={p:cells[p]['measurements'][2] for p in ports}
            if canonical(c['steps'])!=canonical(steps):return False
            matched=[i for i,s in enumerate(plan['solutions']) if s['actions'][:len(actions)]==actions];expected=[];mismatches=[]
            if matched:
                for edge_index in plan['solutions'][matched[0]]['edges'][:len(actions)]:
                    edge=plan['edges'][edge_index];expected.append(deepcopy(plan['nodes'][edge['successor']]['state']))
                for step in range(len(actual)):
                    ports_changed=[p for p in ports if actual[step][p]!=expected[step][p]]
                    if ports_changed:mismatches.append({'step':step,'ports':ports_changed})
            goal_matches=all(actual[-1][p]==v for p,v in goal.items());full=bool(matched) and len(actions)==len(plan['solutions'][matched[0]]['actions']);status='INCOMPLETE_GOAL_OBSERVATION';confirmed={}
            if ordered:status='UNPLANNED_GOAL_SEQUENCE' if not matched else 'UNMODELED_GOAL_RESPONSE' if mismatches else 'GOAL_RESPONSE_CONFIRMED' if full and goal_matches else 'GOAL_PATH_PREFIX_CONFIRMED'
            if status=='GOAL_RESPONSE_CONFIRMED':
                for port,routes in plan['solutions'][matched[0]]['lineage_routes'].items():
                    complete=[]
                    for route in routes:
                        expanded=[]
                        for owner in route:
                            budget.consume()
                            if owner['kind']!='action':expanded.append(deepcopy(owner));continue
                            cell=steps[owner['step']]['cells'][port];position=owner['position'];expanded.append({'kind':'acquired_action','domain':'acquired','step':owner['step'],'port':port,'source':cell['source'],'frame':1,'position':position,'coordinate':deepcopy(cell['occurrences'][1]['coordinates'][position])})
                        complete.append(expanded)
                    confirmed[port]=complete
            result={'status':status,'ordered':bool(ordered),'matched_solutions':matched,'expected_trace':expected,'actual_trace':actual,'mismatches':mismatches,'goal_matches':bool(goal_matches),'confirmed_lineage_routes':confirmed}
            return canonical(c['result'])==canonical(result)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

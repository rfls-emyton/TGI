"""Native action inventory resolved from original latest joint observations."""
from copy import deepcopy
from .identity import decode
from .frame_engine import canonical
from .acquisition_snapshot import acquisition_snapshot as snapshot
from .acquisition_witness import certify_raw_acquisition_witness as certify_acquisition_witness
from .measured_context_layout import layout
from .measured_context import certify_measured_context
from .role_work import RoleSearchBudget


def certify_observed_context_actions(model,groups,measurements,observation,observed_groups,observed_measurements,root_port,anchor_group,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume();groups,measurements,observed_groups,observed_measurements=deepcopy((groups,measurements,observed_groups,observed_measurements))
        trained=snapshot(model);observed=snapshot(observation);learned_witness=certify_acquisition_witness(trained,measurements);state_witness=certify_acquisition_witness(observed,observed_measurements)
        ports,learned_rows=layout(trained,groups,measurements,root_port,budget);observed_ports,rows=layout(observed,observed_groups,observed_measurements,root_port,budget)
        if ports!=observed_ports:raise ValueError('Original interface inventories must match')
        if type(anchor_group) is not int or not 0<=anchor_group<len(rows):raise ValueError('Original group index required')
        anchor=rows[anchor_group];points=[];values={};latest=True;bounds=[]
        for port in ports:
            budget.consume();cell=anchor['cells'][port];point=cell['measurements'][2];bounds.append(point);values[port]=cell['frames'][2]
            point_latest=True
            for index,row in enumerate(rows):
                for frame in (0,2):
                    budget.consume()
                    if index==anchor_group and frame==2:continue
                    other=row['cells'][port]['measurements'][frame]
                    if other['clock']!=point['clock'] or other['upper']>=point['lower']:point_latest=False
            for row in learned_rows:
                for frame in (0,2):
                    budget.consume();other=row['cells'][port]['measurements'][frame]
                    same=frame==2 and canonical(row['cells'][port])==canonical(cell)
                    if same:continue
                    if other['clock']!=point['clock'] or other['upper']>=point['lower']:point_latest=False
            latest &= point_latest
            points.append({'port':port,'source':cell['source'],'occurrence':cell['occurrences'][2],'measurement':point,'latest_in_scope':bool(point_latest)})
        coherent=len({p['clock'] for p in bounds})==1 and max(p['lower'] for p in bounds)<=min(p['upper'] for p in bounds)
        ready=latest and coherent and all(row['certain'] for row in rows)
        inventory=sorted({decode(frames[1]) for frames,_ in trained.episodes.values()});actions=[]
        if ready:
            context={p:values[p] for p in ports if p!=root_port}
            for action in inventory:
                budget.consume();c=certify_measured_context(trained,groups,measurements,root_port,values[root_port],action,context)
                actions.append({'action':action,'certificate':c})
        supported=[r['action'] for r in actions if r['certificate']['result']['status']=='CONTEXTUAL_STRUCTURAL_RESOLUTION']
        return {'policy':'observed_context_actions_v1','root_port':root_port,'anchor_group':anchor_group,'groups':groups,'observed_groups':observed_groups,'learned_witness':learned_witness,'state_witness':state_witness,'ports':ports,'points':points,'state':values,'inventory':inventory,'actions':actions,'result':{'status':'OBSERVED_CONTEXT_ACTIONS_READY' if ready and supported else 'NO_SUPPORTED_ACTION' if ready else 'OBSERVED_STATE_UNRESOLVED','latest_in_scope':bool(latest),'coherent_after':bool(coherent),'supported_actions':supported}}


def certify_observed_action_result(model,groups,measurements,observation,observed_groups,observed_measurements,root_port,anchor_group,plan,acquired,acquired_groups,acquired_measurements,acquired_group,*,max_search_steps=None):
    from .observed_context_actions_check import verify_observed_context_actions
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        if not verify_observed_context_actions(model,groups,measurements,observation,observed_groups,observed_measurements,root_port,anchor_group,plan):raise ValueError('Invalid or stale observed-state plan')
        view=snapshot(acquired);acquired_groups,acquired_measurements=deepcopy((acquired_groups,acquired_measurements));witness=certify_acquisition_witness(view,acquired_measurements);ports,rows=layout(view,acquired_groups,acquired_measurements,root_port,budget)
        if type(acquired_group) is not int or not 0<=acquired_group<len(rows) or ports!=plan['ports']:raise ValueError('Original action group and interface inventory required')
        row=rows[acquired_group];points={p['port']:p for p in plan['points']};ordered=all(r['certain'] for r in rows)
        for port in ports:
            budget.consume();cell=row['cells'][port];previous=points[port]['measurement'];current=cell['measurements'][0]
            ordered &= cell['frames'][0]==plan['state'][port] and current['clock']==previous['clock'] and previous['upper']<current['lower']
        action=row['cells'][root_port]['frames'][1];observed_after=row['cells'][root_port]['frames'][2];selected=next((r for r in plan['actions'] if r['action']==action),None);expected=selected['certificate']['result']['output'] if action in plan['result']['supported_actions'] else []
        status='INCOMPLETE_ACTION_OBSERVATION'
        if ordered:
            status='UNSUPPORTED_ACTION' if not expected else 'CONTEXTUAL_TARGET_RESPONSE_CONFIRMED' if expected==[observed_after] else 'UNMODELED_RESPONSE'
        return {'policy':'observed_context_action_result_v1','plan':deepcopy(plan),'acquired_group':acquired_group,'groups':acquired_groups,'witness':witness,'cells':deepcopy(row['cells']),'result':{'status':status,'ordered':bool(ordered),'action':action,'predicted_output':expected,'observed_output':[observed_after],'observed_state':{p:row['cells'][p]['frames'][2] for p in ports}}}

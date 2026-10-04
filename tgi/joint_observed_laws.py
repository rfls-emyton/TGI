"""Complete endogenous laws predict every acquired interface response."""
from copy import deepcopy
from .observed_joint_state import certify_observed_joint_state
from .measured_context_laws import certify_measured_context_laws
from .acquisition_snapshot import acquisition_snapshot
from .acquisition_witness import certify_raw_acquisition_witness
from .measured_context_layout import layout
from .role_work import RoleSearchBudget


def certify_joint_observed_laws(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume();state=certify_observed_joint_state(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group);laws=[];predicted=[];ready=state['result']['status']=='JOINT_STATE_READY'
        if ready:
            for action in state['inventory']:
                outputs={};supported=True
                for port in state['ports']:
                    budget.consume();context={p:state['state'][p] for p in state['ports'] if p!=port};law=certify_measured_context_laws(model,groups,measurements,port,state['state'][port],action,context);laws.append({'port':port,'action':action,'certificate':law})
                    if law['result']['status']=='MEASURED_CONTEXT_LAW_RESOLVED':outputs[port]=law['result']['output'][0]
                    else:supported=False
                if supported:predicted.append({'action':action,'state':outputs})
        return {'policy':'joint_observed_laws_v1','state_certificate':state,'laws':laws,'result':{'status':'JOINT_ACTIONS_READY' if predicted else 'NO_SUPPORTED_JOINT_ACTION' if ready else 'JOINT_STATE_UNRESOLVED','supported_actions':[r['action'] for r in predicted],'predicted_states':predicted}}


def certify_joint_observed_result(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,plan,acquired,acquired_groups,acquired_measurements,acquired_group,*,max_search_steps=None):
    from .joint_observed_laws_check import verify_joint_observed_laws
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        if not verify_joint_observed_laws(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,plan):raise ValueError('Invalid or stale joint plan')
        acquired_groups,acquired_measurements=deepcopy((acquired_groups,acquired_measurements));view=acquisition_snapshot(acquired);witness=certify_raw_acquisition_witness(view,acquired_measurements);prior=plan['state_certificate'];ports,rows=layout(view,acquired_groups,acquired_measurements,prior['ports'][0],budget)
        if type(acquired_group) is not int or not 0<=acquired_group<len(rows) or ports!=prior['ports']:raise ValueError('Complete original acquired group required')
        cells=rows[acquired_group]['cells'];points={p['port']:p['measurement'] for p in prior['points']};ordered=all(row['certain'] for row in rows)
        for port in ports:
            budget.consume();before=cells[port]['measurements'][0];old=points[port];ordered &= cells[port]['frames'][0]==prior['state'][port] and before['clock']==old['clock'] and old['upper']<before['lower']
        action=cells[ports[0]]['frames'][1];actual={p:cells[p]['frames'][2] for p in ports};selected=next((r for r in plan['result']['predicted_states'] if r['action']==action),None);expected=selected['state'] if selected else {};mismatched=[p for p in ports if expected and expected[p]!=actual[p]]
        status='INCOMPLETE_JOINT_OBSERVATION'
        if ordered:status='UNSUPPORTED_JOINT_ACTION' if not expected else 'UNMODELED_JOINT_RESPONSE' if mismatched else 'JOINT_RESPONSE_CONFIRMED'
        return {'policy':'joint_observed_result_v1','plan':deepcopy(plan),'acquired_group':acquired_group,'groups':acquired_groups,'witness':witness,'cells':deepcopy(cells),'result':{'status':status,'ordered':bool(ordered),'action':action,'predicted_state':deepcopy(expected),'observed_state':actual,'mismatched_ports':mismatched}}

"""Independent complete joint law and all-interface result verification."""
from copy import deepcopy
from .observed_joint_state_check import verify_observed_joint_state
from .measured_context_laws_check import verify_measured_context_laws
from .acquisition_snapshot import acquisition_snapshot
from .acquisition_witness import verify_raw_acquisition_witness
from .measured_context_layout import layout
from .frame_engine import canonical
from .role_work import RoleSearchBudget


def verify_joint_observed_laws(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            c=deepcopy(certificate)
            if set(c)!={'policy','state_certificate','laws','result'} or c['policy']!='joint_observed_laws_v1':return False
            state=c['state_certificate']
            if not verify_observed_joint_state(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,state):return False
            ready=state['result']['status']=='JOINT_STATE_READY';expected_count=len(state['inventory'])*len(state['ports']) if ready else 0
            if len(c['laws'])!=expected_count:return False
            predicted=[];cursor=0
            if ready:
                for action in state['inventory']:
                    output={};supported=True
                    for port in state['ports']:
                        budget.consume();item=c['laws'][cursor];cursor+=1
                        if set(item)!={'port','action','certificate'} or item['port']!=port or item['action']!=action:return False
                        context={p:state['state'][p] for p in state['ports'] if p!=port};law=item['certificate']
                        if not verify_measured_context_laws(model,groups,measurements,port,state['state'][port],action,context,law):return False
                        if law['result']['status']=='MEASURED_CONTEXT_LAW_RESOLVED':output[port]=law['result']['output'][0]
                        else:supported=False
                    if supported:predicted.append({'action':action,'state':output})
            result={'status':'JOINT_ACTIONS_READY' if predicted else 'NO_SUPPORTED_JOINT_ACTION' if ready else 'JOINT_STATE_UNRESOLVED','supported_actions':[r['action'] for r in predicted],'predicted_states':predicted}
            return canonical(c['result'])==canonical(result)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False


def verify_joint_observed_result(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,plan,acquired,acquired_groups,acquired_measurements,acquired_group,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            c=deepcopy(certificate)
            if set(c)!={'policy','plan','acquired_group','groups','witness','cells','result'} or c['policy']!='joint_observed_result_v1' or canonical(c['plan'])!=canonical(plan):return False
            if not verify_joint_observed_laws(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,plan):return False
            if type(acquired_group) is not int or type(c['acquired_group']) is not int or c['acquired_group']!=acquired_group or canonical(c['groups'])!=canonical(acquired_groups):return False
            view=acquisition_snapshot(acquired)
            if not verify_raw_acquisition_witness(view,acquired_measurements,c['witness']):return False
            prior=plan['state_certificate'];ports,rows=layout(view,acquired_groups,acquired_measurements,prior['ports'][0],budget)
            if ports!=prior['ports'] or not 0<=acquired_group<len(rows):return False
            cells=rows[acquired_group]['cells']
            if canonical(c['cells'])!=canonical(cells):return False
            ordered=all(r['certain'] for r in rows);old={r['port']:r['measurement'] for r in prior['points']}
            for port in ports:
                budget.consume();before=cells[port]['measurements'][0];ordered &= cells[port]['frames'][0]==prior['state'][port] and before['clock']==old[port]['clock'] and before['lower']>old[port]['upper']
            action=cells[ports[0]]['frames'][1];actual={p:cells[p]['frames'][2] for p in ports};selected=[r for r in plan['result']['predicted_states'] if r['action']==action];expected=selected[0]['state'] if selected else {};mismatch=[p for p in ports if expected and expected[p]!=actual[p]]
            status='INCOMPLETE_JOINT_OBSERVATION'
            if ordered:status='UNSUPPORTED_JOINT_ACTION' if not expected else 'UNMODELED_JOINT_RESPONSE' if mismatch else 'JOINT_RESPONSE_CONFIRMED'
            result={'status':status,'ordered':bool(ordered),'action':action,'predicted_state':expected,'observed_state':actual,'mismatched_ports':mismatch}
            return canonical(c['result'])==canonical(result)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

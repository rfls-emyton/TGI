"""Independent state binding and complete conditional action verification."""
from copy import deepcopy
from .identity import decode
from .acquisition_snapshot import acquisition_snapshot as snapshot
from .acquisition_witness import verify_raw_acquisition_witness as verify_acquisition_witness
from .measured_context_layout import layout
from .measured_context_check import verify_measured_context
from .frame_engine import canonical
from .role_work import RoleSearchBudget


def verify_observed_context_actions(model,groups,measurements,observation,observed_groups,observed_measurements,root_port,anchor_group,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            c=deepcopy(certificate)
            if set(c)!={'policy','root_port','anchor_group','groups','observed_groups','learned_witness','state_witness','ports','points','state','inventory','actions','result'} or c['policy']!='observed_context_actions_v1':return False
            if type(anchor_group) is not int or c['root_port']!=root_port or type(c['anchor_group']) is not int or c['anchor_group']!=anchor_group or canonical(c['groups'])!=canonical(groups) or canonical(c['observed_groups'])!=canonical(observed_groups):return False
            trained=snapshot(model);observed=snapshot(observation)
            if not verify_acquisition_witness(trained,measurements,c['learned_witness']) or not verify_acquisition_witness(observed,observed_measurements,c['state_witness']):return False
            ports,learned_rows=layout(trained,groups,measurements,root_port,budget);op,rows=layout(observed,observed_groups,observed_measurements,root_port,budget)
            if ports!=op or not 0<=anchor_group<len(rows) or c['ports']!=ports:return False
            values={};points=[];latest=True;intervals=[]
            for port in ports:
                budget.consume();cell=rows[anchor_group]['cells'][port];r=cell['measurements'][2];values[port]=cell['frames'][2];intervals.append(r);good=True
                for index,row in enumerate(rows):
                    for fi in (0,2):
                        budget.consume()
                        if (index,fi)==(anchor_group,2):continue
                        other=row['cells'][port]['measurements'][fi]
                        good &= other['clock']==r['clock'] and other['upper']<r['lower']
                for row in learned_rows:
                    for fi in (0,2):
                        budget.consume();other=row['cells'][port]['measurements'][fi]
                        same=fi==2 and canonical(row['cells'][port])==canonical(cell)
                        if not same:good &= other['clock']==r['clock'] and other['upper']<r['lower']
                latest &= good;points.append({'port':port,'source':cell['source'],'occurrence':cell['occurrences'][2],'measurement':r,'latest_in_scope':bool(good)})
            if canonical(c['state'])!=canonical(values) or canonical(c['points'])!=canonical(points):return False
            coherent=len({r['clock'] for r in intervals})==1 and min(r['upper'] for r in intervals)>=max(r['lower'] for r in intervals)
            ready=latest and coherent and all(r['certain'] for r in rows);inventory=sorted({decode(f[1]) for f,_ in trained.episodes.values()})
            if c['inventory']!=inventory or len(c['actions'])!=(len(inventory) if ready else 0):return False
            supported=[];context={p:values[p] for p in ports if p!=root_port}
            for action,row in zip(inventory,c['actions']):
                budget.consume()
                if set(row)!={'action','certificate'} or row['action']!=action or not verify_measured_context(trained,groups,measurements,root_port,values[root_port],action,context,row['certificate']):return False
                if row['certificate']['result']['status']=='CONTEXTUAL_STRUCTURAL_RESOLUTION':supported.append(action)
            result={'status':'OBSERVED_CONTEXT_ACTIONS_READY' if ready and supported else 'NO_SUPPORTED_ACTION' if ready else 'OBSERVED_STATE_UNRESOLVED','latest_in_scope':bool(latest),'coherent_after':bool(coherent),'supported_actions':supported}
            return canonical(c['result'])==canonical(result)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False


def verify_observed_action_result(model,groups,measurements,observation,observed_groups,observed_measurements,root_port,anchor_group,plan,acquired,acquired_groups,acquired_measurements,acquired_group,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            c=deepcopy(certificate)
            if set(c)!={'policy','plan','acquired_group','groups','witness','cells','result'} or c['policy']!='observed_context_action_result_v1' or canonical(c['plan'])!=canonical(plan):return False
            if not verify_observed_context_actions(model,groups,measurements,observation,observed_groups,observed_measurements,root_port,anchor_group,plan):return False
            if type(acquired_group) is not int or type(c['acquired_group']) is not int or c['acquired_group']!=acquired_group or canonical(c['groups'])!=canonical(acquired_groups):return False
            view=snapshot(acquired)
            if not verify_acquisition_witness(view,acquired_measurements,c['witness']):return False
            ports,rows=layout(view,acquired_groups,acquired_measurements,root_port,budget)
            if ports!=plan['ports'] or not 0<=acquired_group<len(rows):return False
            cells=rows[acquired_group]['cells']
            if canonical(c['cells'])!=canonical(cells):return False
            prior={r['port']:r['measurement'] for r in plan['points']};ordered=all(r['certain'] for r in rows)
            for port in ports:
                budget.consume();current=cells[port]['measurements'][0]
                ordered &= cells[port]['frames'][0]==plan['state'][port] and current['clock']==prior[port]['clock'] and current['lower']>prior[port]['upper']
            action=cells[root_port]['frames'][1];actual=cells[root_port]['frames'][2];expected=[]
            if action in plan['result']['supported_actions']:
                selected=[r for r in plan['actions'] if r['action']==action]
                if len(selected)!=1:return False
                expected=selected[0]['certificate']['result']['output']
            status='INCOMPLETE_ACTION_OBSERVATION'
            if ordered:status='UNSUPPORTED_ACTION' if not expected else 'CONTEXTUAL_TARGET_RESPONSE_CONFIRMED' if expected==[actual] else 'UNMODELED_RESPONSE'
            result={'status':status,'ordered':bool(ordered),'action':action,'predicted_output':expected,'observed_output':[actual],'observed_state':{p:cells[p]['frames'][2] for p in ports}}
            return canonical(c['result'])==canonical(result)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

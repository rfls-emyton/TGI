"""Measured available-action transition and original-query counterevidence."""
from copy import deepcopy
from .observed_actuation_discovery_check import verify_observed_actuation_discovery
from .acquisition_snapshot import acquisition_snapshot
from .acquisition_witness import certify_raw_acquisition_witness
from .observed_joint_state import certify_observed_joint_state
from .compact_role_observation import certify_compact_role_constraints
from .joint_frontier_acquisition import _rebuild
from .measured_context_layout import layout
from .frame_engine import canonical
from .identity import decode
from .role_work import RoleSearchBudget

from .observed_actuation_learning import rebuild_discovery_history
from .measured_context_laws import certify_measured_context_laws

def prepare_measured_actuation_transition(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,catalogue,catalogue_measurements,plan,action_index,acquired,acquired_groups,acquired_measurements,acquired_group,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume();plan,acquired_groups,acquired_measurements=deepcopy((plan,acquired_groups,acquired_measurements));args=(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,catalogue,catalogue_measurements)
        if not verify_observed_actuation_discovery(*args,plan):raise ValueError('Original verified discovery plan required')
        if not plan['result']['catalogue_current'] or type(action_index) is not int or not 0<=action_index<len(plan['available_actions']):raise ValueError('Current original available action index required')
        selected=plan['available_actions'][action_index];predicted=next((deepcopy(x['state']) for x in plan['result']['predicted_states'] if x['action']==selected),None)
        view=acquisition_snapshot(acquired);old=acquisition_snapshot(observation);trained=acquisition_snapshot(model)
        if canonical(acquired_groups[:len(observed_groups)])!=canonical(observed_groups):raise ValueError('Retain all original observation groups')
        lookup={(r['source'],r['frame'],r['start'],r['stop']):r for r in acquired_measurements}
        for source,episode in old.episodes.items():
            budget.consume()
            if view.episodes.get(source)!=episode:raise ValueError('Retain original observed episodes')
        for r in observed_measurements:
            budget.consume()
            if lookup.get((r['source'],r['frame'],r['start'],r['stop']))!=r:raise ValueError('Retain original measurements')
        state=plan['state_certificate'];witness=certify_raw_acquisition_witness(view,acquired_measurements);ports,rows=layout(view,acquired_groups,acquired_measurements,state['ports'][0],budget,allow_partial=True)
        if ports!=state['ports'] or type(acquired_group) is not int or not len(observed_groups)<=acquired_group<len(rows) or set(rows[acquired_group]['cells'])!=set(ports):raise ValueError('New complete original group required')
        row=rows[acquired_group];cells=row['cells'];before={p:cells[p]['frames'][0] for p in ports};actual={p:cells[p]['frames'][2] for p in ports};action=cells[ports[0]]['frames'][1];requested={'action':selected,'before':state['state']};ordered=row['certain'];points={p['port']:p['measurement'] for p in state['points']}
        for port in ports:
            b=cells[port]['measurements'][0];previous=points[port];budget.consume();ordered &= b['clock']==previous['clock'] and b['lower']>previous['upper']
            for record in plan['catalogue_records']:
                budget.consume();a=record['measurement'];ordered &= a['clock']==b['clock'] and a['upper']<b['lower']
        matches=action==requested['action'] and before==requested['before'];admitted=bool(ordered and matches);after=None;history=None;next_state=None;roles=None;prior_queries=None
        if admitted:
            after,history=rebuild_discovery_history(trained,groups,measurements,view,acquired_groups,acquired_measurements,budget)
            limits=[];current=budget
            while current is not None:
                if current.limit is not None:limits.append(max(0,current.limit-current.used))
                current=getattr(current,'parent',None)
            from .incremental import FormationSearchLimit
            try:after.form(max_search_steps=min(limits) if limits else None)
            except FormationSearchLimit as error:budget.consume_many(error.used);budget.consume();raise
            budget.consume_many(after.formation_work['search_steps']);next_state=certify_observed_joint_state(after,history['groups'],history['measurements'],after,history['groups'],history['measurements'],history.get('acquired_group_indices',list(range(len(groups),len(groups)+len(acquired_groups))))[acquired_group]);roles=certify_compact_role_constraints(after,history['groups'],history['measurements'])
            prior_queries=[]
            for port in ports:
                budget.consume();context={p:state['state'][p] for p in ports if p!=port};prior_queries.append({'port':port,'certificate':certify_measured_context_laws(after,history['groups'],history['measurements'],port,state['state'][port],selected,context)})
        outcome='NOT_EVALUATED' if not admitted else 'UNRESOLVED' if predicted is None else 'MATCHED' if actual==predicted else 'CONTRADICTED'
        result={'status':'ACTUATION_TRANSITION_ADMITTED' if admitted else 'UNPLANNED_ACTUATION_EXPERIENCE' if not matches else 'INCOMPLETE_ACTUATION_EXPERIENCE','ordered':bool(ordered),'requested_before_and_action_match':bool(matches),'experience_admitted':admitted,'actual_state':actual,'next_state_status':None if next_state is None else next_state['result']['status'],'prediction_outcome':outcome}
        return after,{'policy':'measured_actuation_transition_v1','plan':plan,'action_index':action_index,'acquired_group':acquired_group,'selected_action':selected,'predicted_state':predicted,'prior_query_laws':prior_queries,'groups':acquired_groups,'witness':witness,'cells':deepcopy(cells),'history':history,'next_state':next_state,'roles':roles,'result':result}

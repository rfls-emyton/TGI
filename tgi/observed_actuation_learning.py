"""Verified first-actuation experience and original native knowledge successor."""
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



def rebuild_discovery_history(trained,groups,measurements,view,acquired_groups,acquired_measurements,budget):
    # Reuse only the same complete measured original source prefix, never equal values.
    prefix=len(groups);shared=bool(prefix) and canonical(acquired_groups[:prefix])==canonical(groups) and canonical(acquired_measurements[:len(measurements)])==canonical(measurements)
    for source,episode in trained.episodes.items():
        budget.consume();shared &= view.episodes.get(source)==episode
    if not shared:return _rebuild(trained,groups,measurements,view,acquired_groups,acquired_measurements,budget)
    from .organization import RawOrganization
    combined=RawOrganization();mapping=[];raw=[];names={};gs=[];ms=[]
    for ordinal,(source,(frames,_)) in enumerate(trained.episodes.items()):
        name=canonical(['learned',ordinal]);budget.consume_many(sum(map(len,frames))+len(source)+len(name)+1);names[source]=name;values=list(map(decode,frames));combined.observe(name,values);mapping.append({'domain':'learned','ordinal':ordinal,'original_source':source,'source':name});raw.append({'source':name,'frames':values})
    for ordinal,(source,(frames,_)) in enumerate(view.episodes.items()):
        budget.consume_many(sum(map(len,frames))+len(source)+1)
        if source not in names:
            name=canonical(['acquired',ordinal]);names[source]=name;values=list(map(decode,frames));combined.observe(name,values);raw.append({'source':name,'frames':values})
        mapping.append({'domain':'acquired','ordinal':ordinal,'original_source':source,'source':names[source]})
    for group in acquired_groups:
        budget.consume_many(len(group)+1);gs.append([{'port':x['port'],'source':names[x['source']]} for x in group])
    for record in acquired_measurements:budget.consume();ms.append({**deepcopy(record),'source':names[record['source']]})
    return combined,{'policy':'joint_history_verified_overlap_v1','retained_acquired_prefix_groups':prefix,'acquired_group_indices':list(range(len(acquired_groups))),'source_map':mapping,'episodes':raw,'groups':gs,'measurements':ms}


def prepare_observed_actuation_learning(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,catalogue,catalogue_measurements,plan,request_index,acquired,acquired_groups,acquired_measurements,acquired_group,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume();plan,acquired_groups,acquired_measurements=deepcopy((plan,acquired_groups,acquired_measurements));args=(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,catalogue,catalogue_measurements)
        if not verify_observed_actuation_discovery(*args,plan):raise ValueError('Original verified discovery plan required')
        if type(request_index) is not int or not 0<=request_index<len(plan['requests']):raise ValueError('Original request index required')
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
        row=rows[acquired_group];cells=row['cells'];before={p:cells[p]['frames'][0] for p in ports};actual={p:cells[p]['frames'][2] for p in ports};action=cells[ports[0]]['frames'][1];request=plan['requests'][request_index];ordered=row['certain'];points={p['port']:p['measurement'] for p in state['points']}
        for port in ports:
            b=cells[port]['measurements'][0];previous=points[port];budget.consume();ordered &= b['clock']==previous['clock'] and b['lower']>previous['upper']
            for record in plan['catalogue_records']:
                budget.consume();a=record['measurement'];ordered &= a['clock']==b['clock'] and a['upper']<b['lower']
        matches=action==request['action'] and before==request['before'];admitted=bool(ordered and matches);after=None;history=None;next_state=None;roles=None
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
        result={'status':'ACTUATION_EXPERIENCE_ADMITTED' if admitted else 'UNPLANNED_ACTUATION_EXPERIENCE' if not matches else 'INCOMPLETE_ACTUATION_EXPERIENCE','ordered':bool(ordered),'requested_before_and_action_match':bool(matches),'experience_admitted':admitted,'actual_state':actual,'next_state_status':None if next_state is None else next_state['result']['status']}
        return after,{'policy':'observed_actuation_learning_v1','plan':plan,'request_index':request_index,'acquired_group':acquired_group,'groups':acquired_groups,'witness':witness,'cells':deepcopy(cells),'history':history,'next_state':next_state,'roles':roles,'result':result}

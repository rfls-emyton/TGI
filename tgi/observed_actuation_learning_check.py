"""Independent raw lineage, timing, native inventory and acquired state checker."""
from copy import deepcopy
from .observed_actuation_discovery_check import verify_observed_actuation_discovery
from .acquisition_snapshot import acquisition_snapshot
from .acquisition_witness import verify_raw_acquisition_witness
from .observed_joint_state_check import verify_observed_joint_state
from .compact_role_observation_check import verify_compact_role_constraints
from .organization_snapshot import snapshot
from .organization_inventory_check import verify_organization_inventory
from .measured_context_layout import layout
from .identity import decode
from .frame_engine import canonical
from .role_work import RoleSearchBudget


def verify_observed_actuation_learning(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,catalogue,catalogue_measurements,plan,request_index,acquired,acquired_groups,acquired_measurements,acquired_group,after,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            c=deepcopy(certificate);args=(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,catalogue,catalogue_measurements)
            if set(c)!={'policy','plan','request_index','acquired_group','groups','witness','cells','history','next_state','roles','result'} or c['policy']!='observed_actuation_learning_v1':return False
            if not verify_observed_actuation_discovery(*args,plan) or canonical(c['plan'])!=canonical(plan) or type(request_index) is not int or not 0<=request_index<len(plan['requests']) or type(c['request_index']) is not int or c['request_index']!=request_index:return False
            if type(acquired_group) is not int or type(c['acquired_group']) is not int or c['acquired_group']!=acquired_group or canonical(c['groups'])!=canonical(acquired_groups):return False
            trained=acquisition_snapshot(model);view=acquisition_snapshot(acquired);old=acquisition_snapshot(observation)
            if canonical(acquired_groups[:len(observed_groups)])!=canonical(observed_groups):return False
            lookup={(r['source'],r['frame'],r['start'],r['stop']):r for r in acquired_measurements}
            for source,episode in old.episodes.items():
                budget.consume()
                if view.episodes.get(source)!=episode:return False
            for r in observed_measurements:
                budget.consume()
                if lookup.get((r['source'],r['frame'],r['start'],r['stop']))!=r:return False
            if not verify_raw_acquisition_witness(view,acquired_measurements,c['witness']):return False
            state=plan['state_certificate'];ports,rows=layout(view,acquired_groups,acquired_measurements,state['ports'][0],budget,allow_partial=True)
            if ports!=state['ports'] or not len(observed_groups)<=acquired_group<len(rows) or set(rows[acquired_group]['cells'])!=set(ports):return False
            row=rows[acquired_group];cells=row['cells']
            if canonical(c['cells'])!=canonical(cells):return False
            before={p:cells[p]['frames'][0] for p in ports};actual={p:cells[p]['frames'][2] for p in ports};action=cells[ports[0]]['frames'][1];request=plan['requests'][request_index];ordered=row['certain'];points={p['port']:p['measurement'] for p in state['points']}
            for port in ports:
                budget.consume();b=cells[port]['measurements'][0];p=points[port];ordered &= b['clock']==p['clock'] and p['upper']<b['lower']
                for record in plan['catalogue_records']:
                    budget.consume();a=record['measurement'];ordered &= a['clock']==b['clock'] and a['upper']<b['lower']
            matches=action==request['action'] and before==request['before'];admitted=bool(ordered and matches)
            if admitted:
                prefix=len(groups);reuse=bool(prefix) and canonical(acquired_groups[:prefix])==canonical(groups) and canonical(acquired_measurements[:len(measurements)])==canonical(measurements)
                for source,episode in trained.episodes.items():
                    budget.consume();reuse &= view.episodes.get(source)==episode
                raw=[];mapping=[];gs=[];ms=[];episodes={};learned_names={}
                for domain,parent,parent_groups,parent_measurements in [('learned',trained,groups,measurements),('acquired',view,acquired_groups,acquired_measurements)]:
                    names={}
                    for ordinal,(source,(frames,_)) in enumerate(parent.episodes.items()):
                        name=learned_names[source] if reuse and domain=='acquired' and source in learned_names else canonical([domain,ordinal]);budget.consume_many(sum(map(len,frames))+len(source)+len(name)+1);names[source]=name;mapping.append({'domain':domain,'ordinal':ordinal,'original_source':source,'source':name})
                        if name not in episodes:raw.append({'source':name,'frames':list(map(decode,frames))});episodes[name]=frames
                    if domain=='learned':learned_names=names.copy()
                    if reuse and domain=='learned':continue
                    for group in parent_groups:budget.consume_many(len(group)+1);gs.append([{'port':x['port'],'source':names[x['source']]} for x in group])
                    for record in parent_measurements:budget.consume();ms.append({**deepcopy(record),'source':names[record['source']]})
                history={'policy':'joint_history_ordinal_v1','source_map':mapping,'episodes':raw,'groups':gs,'measurements':ms}
                if reuse:history.update(policy='joint_history_verified_overlap_v1',retained_acquired_prefix_groups=prefix,acquired_group_indices=list(range(len(acquired_groups))))
                current_anchor=acquired_group if reuse else len(groups)+acquired_group
                if canonical(c['history'])!=canonical(history) or after is None:return False
                target=acquisition_snapshot(after)
                if set(target.episodes)!=set(episodes) or any(target.episodes[s][0]!=frames for s,frames in episodes.items()):return False
                if not verify_organization_inventory(snapshot(after)):return False
                if not verify_observed_joint_state(after,gs,ms,after,gs,ms,current_anchor,c['next_state']) or not verify_compact_role_constraints(after,gs,ms,c['roles']):return False
                next_status=c['next_state']['result']['status']
            else:
                if after is not None or any(c[k] is not None for k in ('history','next_state','roles')):return False
                next_status=None
            result={'status':'ACTUATION_EXPERIENCE_ADMITTED' if admitted else 'UNPLANNED_ACTUATION_EXPERIENCE' if not matches else 'INCOMPLETE_ACTUATION_EXPERIENCE','ordered':bool(ordered),'requested_before_and_action_match':bool(matches),'experience_admitted':admitted,'actual_state':actual,'next_state_status':next_status}
            return canonical(c['result'])==canonical(result)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

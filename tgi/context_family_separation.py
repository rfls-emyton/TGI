"""Endogenous measured-family separating requests; complete original witnesses retained."""
from copy import deepcopy
from tgi.identity import encode
from tgi.frame_engine import canonical
from tgi.role_work import RoleSearchBudget
from tgi.observed_actuation_discovery import certify_observed_actuation_discovery
from tgi.observed_actuation_discovery_check import verify_observed_actuation_discovery

def certify_context_family_separation(*args,discovery=None,max_search_steps=None):
 b=RoleSearchBudget(max_search_steps)
 with b.scope():
  b.consume()
  if discovery is None:d=certify_observed_actuation_discovery(*args)
  else:
   if not verify_observed_actuation_discovery(*args,discovery):raise ValueError('Complete original current discovery required')
   d=deepcopy(discovery)
  laws=[];obligations=[];requests=[]
  state=d['state_certificate'];ready=state['result']['status']=='JOINT_STATE_READY';current=d['result']['catalogue_current']
  if not ready:obligations.append({'kind':'ACTUAL_STATE_UNRESOLVED'})
  if not current:obligations.append({'kind':'CATALOGUE_NOT_CURRENT'})
  by_action={action:[] for action in d['available_actions']}
  for li,item in enumerate(d['laws']):
   b.consume();parent=item['certificate'];c=parent['law'] if parent['policy']=='observation_context_laws_v1' else parent
   certain=parent['result']['status']!='INCOMPLETE_OBSERVATION' and all(row['certain'] for row in c['rows']);uncontradicted=not c['local_conflicts'];forecasts=[];partitions={};unknown=[];pairs=[]
   if not certain:obligations.append({'kind':'UNCERTAIN_ORIGINAL_ROWS','law':li})
   if not uncontradicted:obligations.append({'kind':'CONTRADICTED_ORIGINAL_INPUT','law':li})
   for ci,candidate in enumerate(c['candidates']):
    b.consume();values=candidate['conclusions'];valid=candidate['resolved'] and len(values)==1 and len(values[0])==1 and isinstance(values[0][0],str) and bool(values[0][0]);ids=list(encode(values[0][0])) if valid else None
    forecasts.append({'candidate_index':ci,'ports':deepcopy(candidate['ports']),'source_scope':deepcopy(candidate['source_scope']),'output_ids':ids,'status':'SOURCE_BOUND_FORECAST' if valid else 'OUTCOME_OBLIGATION_OPEN'})
    if valid:partitions.setdefault(tuple(ids),[]).append(ci)
    else:unknown.append(ci);obligations.append({'kind':'FAMILY_FORECAST_UNRESOLVED','law':li,'candidate':ci})
   if certain and uncontradicted:
    for left in range(len(forecasts)):
     for right in range(left+1,len(forecasts)):
      b.consume();x,y=forecasts[left]['output_ids'],forecasts[right]['output_ids']
      if x is not None and y is not None and x!=y:pairs.append({'left':left,'right':right})
   row={'law_index':li,'action':item['action'],'port':item['port'],'certain_original_rows':bool(certain),'uncontradicted_current_input':bool(uncontradicted),'forecasts':forecasts,'partitions':[{'output_ids':list(ids),'candidate_indexes':indexes} for ids,indexes in sorted(partitions.items())],'unresolved_candidates':unknown,'separating_pairs':pairs};laws.append(row)
   if pairs:by_action[item['action']].append({'law_index':li,'port':item['port'],'pairs':deepcopy(pairs),'complete_family_predictions':not bool(unknown)})
  for action in d['available_actions']:
   b.consume()
   if by_action[action]:requests.append({'action':action,'action_ids':list(encode(action)),'before':deepcopy(state['state']),'port_contrasts':by_action[action]})
  eligible=[r['action'] for r in requests];status='ACTUAL_STATE_UNRESOLVED' if not ready else 'CATALOGUE_NOT_CURRENT' if not current else 'SEPARATING_REQUESTS_READY' if requests else 'SEPARATION_OBLIGATIONS_OPEN' if obligations else 'NO_CURRENT_FAMILY_SEPARATOR'
  return {'policy':'context_family_separation_v1','discovery':d,'laws':laws,'requests':requests,'obligations':obligations,'result':{'status':status,'eligible_actions':eligible,'unique_admitted_action':eligible[0] if len(eligible)==1 else None,'request_count':len(requests),'all_current_forecast_obligations_closed':not bool(obligations),'actual_outcome_acquired':False}}

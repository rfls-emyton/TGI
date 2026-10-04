"""Independent complete measured-family partition and contrast verification."""
from copy import deepcopy
from tgi.frame_engine import canonical
from tgi.identity import encode
from tgi.role_work import RoleSearchBudget
from tgi.observed_actuation_discovery_check import verify_observed_actuation_discovery

def verify_context_family_separation(*args,certificate,max_search_steps=None):
 b=RoleSearchBudget(max_search_steps)
 with b.scope():
  b.consume()
  try:
   if type(certificate) is not dict or set(certificate)!={'policy','discovery','laws','requests','obligations','result'} or certificate['policy']!='context_family_separation_v1':return False
   d=certificate['discovery']
   if not verify_observed_actuation_discovery(*args,d):return False
   expected=[];pending=[];available=d['available_actions'];action_ports={action:[] for action in available};state=d['state_certificate'];ready=state['result']['status']=='JOINT_STATE_READY';fresh=d['result']['catalogue_current']
   if not ready:pending.append({'kind':'ACTUAL_STATE_UNRESOLVED'})
   if not fresh:pending.append({'kind':'CATALOGUE_NOT_CURRENT'})
   for index in range(len(d['laws'])):
    b.consume();item=d['laws'][index];outer=item['certificate'];law=outer['law'] if outer['policy']=='observation_context_laws_v1' else outer;certain=outer['result']['status']!='INCOMPLETE_OBSERVATION' and all(r['certain'] for r in law['rows']);consistent=len(law['local_conflicts'])==0;items=[];open_indexes=[]
    if not certain:pending.append({'kind':'UNCERTAIN_ORIGINAL_ROWS','law':index})
    if not consistent:pending.append({'kind':'CONTRADICTED_ORIGINAL_INPUT','law':index})
    for j in range(len(law['candidates'])):
     b.consume();candidate=law['candidates'][j];out=None
     if candidate['resolved'] and len(candidate['conclusions'])==1:
      outcome=candidate['conclusions'][0]
      if len(outcome)==1 and isinstance(outcome[0],str) and len(outcome[0])>0:out=[x for x in encode(outcome[0])]
     items.append({'candidate_index':j,'ports':deepcopy(candidate['ports']),'source_scope':deepcopy(candidate['source_scope']),'output_ids':out,'status':'SOURCE_BOUND_FORECAST' if out is not None else 'OUTCOME_OBLIGATION_OPEN'})
     if out is None:open_indexes.append(j);pending.append({'kind':'FAMILY_FORECAST_UNRESOLVED','law':index,'candidate':j})
    partitions=[];unique=sorted({tuple(v['output_ids']) for v in items if v['output_ids'] is not None})
    for ids in unique:
     b.consume();partitions.append({'output_ids':list(ids),'candidate_indexes':[j for j,v in enumerate(items) if v['output_ids']==list(ids)]})
    pairs=[]
    if certain and consistent:
     for j,item_left in enumerate(items):
      for k in range(j+1,len(items)):
       b.consume();lhs,rhs=item_left['output_ids'],items[k]['output_ids']
       if lhs is not None and rhs is not None and lhs!=rhs:pairs.append({'left':j,'right':k})
    expected.append({'law_index':index,'action':item['action'],'port':item['port'],'certain_original_rows':bool(certain),'uncontradicted_current_input':bool(consistent),'forecasts':items,'partitions':partitions,'unresolved_candidates':open_indexes,'separating_pairs':pairs})
    if pairs:action_ports[item['action']].append({'law_index':index,'port':item['port'],'pairs':deepcopy(pairs),'complete_family_predictions':not bool(open_indexes)})
   requests=[]
   for action in available:
    b.consume()
    if action_ports[action]:requests.append({'action':action,'action_ids':list(encode(action)),'before':deepcopy(state['state']),'port_contrasts':action_ports[action]})
   actions=[v['action'] for v in requests];status='ACTUAL_STATE_UNRESOLVED' if not ready else 'CATALOGUE_NOT_CURRENT' if not fresh else 'SEPARATING_REQUESTS_READY' if requests else 'SEPARATION_OBLIGATIONS_OPEN' if pending else 'NO_CURRENT_FAMILY_SEPARATOR';result={'status':status,'eligible_actions':actions,'unique_admitted_action':actions[0] if len(actions)==1 else None,'request_count':len(requests),'all_current_forecast_obligations_closed':not bool(pending),'actual_outcome_acquired':False}
   return canonical(certificate['laws'])==canonical(expected) and canonical(certificate['requests'])==canonical(requests) and canonical(certificate['obligations'])==canonical(pending) and canonical(certificate['result'])==canonical(result)
  except (KeyError,ValueError,TypeError,IndexError,AttributeError):return False

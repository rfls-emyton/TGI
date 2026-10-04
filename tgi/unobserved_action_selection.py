"""Source-complete acquisition coverage choice before a separator is observable."""
from copy import deepcopy
from hashlib import sha256
from tgi.frame_engine import canonical
from tgi.identity import encode
from tgi.role_work import RoleSearchBudget
from tgi.guarded_word_goal_frontier_check import verify_guarded_word_goal_frontier
from tgi.guarded_word_goal_workflow import GuardedWordGoalWorkflow

def certify_unobserved_action_selection(*args,frontier,max_search_steps=None):
 b=RoleSearchBudget(max_search_steps)
 with b.scope():
  b.consume();frontier=deepcopy(frontier)
  if not verify_guarded_word_goal_frontier(*args,goal=frontier['goal'],certificate=frontier,max_depth=frontier['max_depth']):raise ValueError('Complete original current task frontier required')
  d=frontier['discovery'];coverage=[];bindings=[]
  for action in d['available_actions']:
   witnesses=[]
   for li,item in enumerate(d['laws']):
    if item['action']!=action:continue
    c=item['certificate'];c=c['law'] if c['policy']=='observation_context_laws_v1' else c;matching=[]
    for ri,row in enumerate(c['rows']):
     b.consume()
     if row['cells'][item['port']]['frames'][1]==action:matching.append(ri)
    witnesses.append({'law_index':li,'port':item['port'],'matching_original_rows':matching})
   unobserved=bool(witnesses) and len(witnesses)==len(d['state_certificate']['ports']) and all(not w['matching_original_rows'] for w in witnesses)
   coverage.append({'action':action,'action_ids':list(encode(action)),'source_coverage':witnesses,'unobserved':unobserved})
   indexes=[]
   for ci,choice in enumerate(frontier['choices']):
    b.consume()
    if unobserved and choice['kind']=='FRONTIER_EXPERIENCE' and choice['actions']==[action] and len(choice['edges'])==1 and frontier['frontier']['edges'][choice['edges'][0]]['source']==0:indexes.append(ci)
   if unobserved:bindings.append({'action':action,'choice_indexes':indexes})
  ready=d['result']['catalogue_current'] and d['state_certificate']['result']['status']=='JOINT_STATE_READY'
  eligible=[row for row in bindings if len(row['choice_indexes'])==1];unique=ready and len(bindings)==1 and len(eligible)==1
  status='UNIQUE_UNOBSERVED_ACTION_SELECTION_READY' if unique else 'UNOBSERVED_ACTION_ALTERNATIVES_RETAINED' if bindings else 'NO_CURRENT_UNOBSERVED_ACTION'
  return {'policy':'unobserved_action_selection_v1','frontier_sha256':sha256(canonical(frontier).encode()).hexdigest(),'coverage':coverage,'bindings':bindings,'result':{'status':status,'selected_action':eligible[0]['action'] if unique else None,'selected_choice_index':eligible[0]['choice_indexes'][0] if unique else None,'effect_predicted':False,'separation_claimed':False}}

def select_unique_unobserved_action(workflow,*,max_search_steps=None):
 from tgi.unobserved_action_selection_check import verify_unobserved_action_selection
 b=RoleSearchBudget(max_search_steps)
 with b.scope():
  b.consume()
  if type(workflow) is not GuardedWordGoalWorkflow or workflow.pending()['status']!='SELECTION_REQUIRED':raise ValueError('Owned unselected current workflow required')
  args=workflow.context();f=workflow.frontier();c=certify_unobserved_action_selection(*args,frontier=f)
  if not verify_unobserved_action_selection(*args,frontier=f,certificate=c) or c['result']['status']!='UNIQUE_UNOBSERVED_ACTION_SELECTION_READY':raise ValueError('Unique independently checked current acquisition obligation required')
  result=workflow.select(c['result']['selected_choice_index'])
  if result.pending()['action']!=c['result']['selected_action']:raise ValueError('Actual selection binding mismatch')
  return result,c

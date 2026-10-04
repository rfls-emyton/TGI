"""Bind an endogenous unique family separator to an owned actual workflow choice."""
from copy import deepcopy
from hashlib import sha256
from tgi.frame_engine import canonical
from tgi.role_work import RoleSearchBudget
from tgi.guarded_word_goal_workflow import GuardedWordGoalWorkflow
from tgi.guarded_word_goal_frontier_check import verify_guarded_word_goal_frontier
from tgi.context_family_separation import certify_context_family_separation
from tgi.context_family_separation_check import verify_context_family_separation

def certify_context_family_selection(*args,frontier,separation=None,max_search_steps=None):
 b=RoleSearchBudget(max_search_steps)
 with b.scope():
  b.consume();frontier=deepcopy(frontier)
  if not verify_guarded_word_goal_frontier(*args,goal=frontier['goal'],certificate=frontier,max_depth=frontier['max_depth']):raise ValueError('Original complete current guarded-word frontier required')
  if separation is None:s=certify_context_family_separation(*args,discovery=frontier['discovery'])
  else:
   if not verify_context_family_separation(*args,certificate=separation):raise ValueError('Complete current native separator required')
   s=deepcopy(separation)
  if canonical(s['discovery'])!=canonical(frontier['discovery']):raise ValueError('Same complete original current discovery required')
  bindings=[]
  for ri,request in enumerate(s['requests']):
   indexes=[]
   for ci,choice in enumerate(frontier['choices']):
    b.consume()
    if choice['kind']=='FRONTIER_EXPERIENCE' and choice['actions']==[request['action']] and len(choice['edges'])==1 and frontier['frontier']['edges'][choice['edges'][0]]['source']==0:indexes.append(ci)
   bindings.append({'request_index':ri,'action':request['action'],'choice_indexes':indexes})
  selected_request=None;selected_choice=None;action=s['result']['unique_admitted_action'];status='NO_ADMITTED_SEPARATING_ACTION' if not bindings else 'DISTINGUISHING_ALTERNATIVES_REQUIRE_SELECTION' if action is None else 'SEPARATING_ACTION_OUTSIDE_CURRENT_TASK_FRONTIER'
  if action is not None:
   row=next(v for v in bindings if v['action']==action)
   if len(row['choice_indexes'])==1:selected_request=row['request_index'];selected_choice=row['choice_indexes'][0];status='UNIQUE_NATIVE_SEPARATOR_SELECTION_READY'
  return {'policy':'context_family_selection_v1','separation':s,'workflow_frontier_sha256':sha256(canonical(frontier).encode()).hexdigest(),'bindings':bindings,'result':{'status':status,'selected_request_index':selected_request,'selected_choice_index':selected_choice,'selected_action':action if selected_choice is not None else None}}

def select_unique_context_family_separator(workflow,*,separation=None,max_search_steps=None):
 from tgi.context_family_selection_check import verify_context_family_selection
 b=RoleSearchBudget(max_search_steps)
 with b.scope():
  b.consume()
  if type(workflow) is not GuardedWordGoalWorkflow or workflow.pending()['status']!='SELECTION_REQUIRED':raise ValueError('Original owned unselected native workflow required')
  args=workflow.context();frontier=workflow.frontier();certificate=certify_context_family_selection(*args,frontier=frontier,separation=separation)
  if not verify_context_family_selection(*args,frontier=frontier,certificate=certificate):raise ValueError('Independent original separator selection verification failed')
  if certificate['result']['status']!='UNIQUE_NATIVE_SEPARATOR_SELECTION_READY':raise ValueError('A unique structurally admitted current task separator is required; alternatives retained in certificate')
  successor=workflow.select(certificate['result']['selected_choice_index'])
  if successor.pending()['action']!=certificate['result']['selected_action']:raise ValueError('Original selected action binding mismatch')
  return successor,certificate

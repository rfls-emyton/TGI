"""Independent source/frontier/action-to-choice binding; no producer or execution."""
from copy import deepcopy
from hashlib import sha256
from tgi.frame_engine import canonical
from tgi.role_work import RoleSearchBudget
from tgi.guarded_word_goal_frontier_check import verify_guarded_word_goal_frontier
from tgi.context_family_separation_check import verify_context_family_separation

def verify_context_family_selection(*args,frontier,certificate,max_search_steps=None):
 b=RoleSearchBudget(max_search_steps)
 with b.scope():
  b.consume()
  try:
   if type(certificate) is not dict or set(certificate)!={'policy','separation','workflow_frontier_sha256','bindings','result'} or certificate['policy']!='context_family_selection_v1':return False
   if not verify_guarded_word_goal_frontier(*args,goal=frontier['goal'],certificate=frontier,max_depth=frontier['max_depth']):return False
   s=certificate['separation']
   if not verify_context_family_separation(*args,certificate=s) or canonical(s['discovery'])!=canonical(frontier['discovery']) or certificate['workflow_frontier_sha256']!=sha256(canonical(frontier).encode()).hexdigest():return False
   bindings=[]
   for ri in range(len(s['requests'])):
    action=s['requests'][ri]['action'];indexes=[]
    for ci in range(len(frontier['choices'])):
     b.consume();choice=frontier['choices'][ci]
     if choice['kind']!='FRONTIER_EXPERIENCE' or choice['actions']!=[action] or len(choice['edges'])!=1:continue
     if frontier['frontier']['edges'][choice['edges'][0]]['source']==0:indexes.append(ci)
    bindings.append({'request_index':ri,'action':action,'choice_indexes':indexes})
   request=None;index=None;action=s['result']['unique_admitted_action'];status='NO_ADMITTED_SEPARATING_ACTION' if not bindings else 'DISTINGUISHING_ALTERNATIVES_REQUIRE_SELECTION' if action is None else 'SEPARATING_ACTION_OUTSIDE_CURRENT_TASK_FRONTIER'
   if action is not None:
    eligible=[v for v in bindings if v['action']==action]
    if len(eligible)!=1:return False
    if len(eligible[0]['choice_indexes'])==1:request=eligible[0]['request_index'];index=eligible[0]['choice_indexes'][0];status='UNIQUE_NATIVE_SEPARATOR_SELECTION_READY'
   result={'status':status,'selected_request_index':request,'selected_choice_index':index,'selected_action':action if index is not None else None};return canonical(certificate['bindings'])==canonical(bindings) and canonical(certificate['result'])==canonical(result)
  except (KeyError,ValueError,TypeError,IndexError,AttributeError):return False

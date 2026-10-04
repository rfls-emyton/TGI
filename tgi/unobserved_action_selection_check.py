"""Independent complete original-row coverage and owned frontier selection verifier."""
from hashlib import sha256
from tgi.frame_engine import canonical
from tgi.identity import encode
from tgi.role_work import RoleSearchBudget
from tgi.guarded_word_goal_frontier_check import verify_guarded_word_goal_frontier

def verify_unobserved_action_selection(*args,frontier,certificate,max_search_steps=None):
 b=RoleSearchBudget(max_search_steps)
 with b.scope():
  b.consume()
  try:
   if type(certificate) is not dict or set(certificate)!={'policy','frontier_sha256','coverage','bindings','result'} or certificate['policy']!='unobserved_action_selection_v1':return False
   if not verify_guarded_word_goal_frontier(*args,goal=frontier['goal'],certificate=frontier,max_depth=frontier['max_depth']):return False
   if certificate['frontier_sha256']!=sha256(canonical(frontier).encode()).hexdigest():return False
   discovery=frontier['discovery'];coverage=[];bindings=[]
   for action in discovery['available_actions']:
    sources=[]
    for li in range(len(discovery['laws'])):
     law=discovery['laws'][li]
     if law['action']!=action:continue
     c=law['certificate'];c=c['law'] if c['policy']=='observation_context_laws_v1' else c;indexes=[]
     for ri in range(len(c['rows'])):
      b.consume()
      if c['rows'][ri]['cells'][law['port']]['frames'][1]==action:indexes.append(ri)
     sources.append({'law_index':li,'port':law['port'],'matching_original_rows':indexes})
    missing=len(sources)==len(discovery['state_certificate']['ports']) and bool(sources) and not any(row['matching_original_rows'] for row in sources)
    coverage.append({'action':action,'action_ids':list(encode(action)),'source_coverage':sources,'unobserved':missing})
    choices=[]
    for ci in range(len(frontier['choices'])):
     b.consume();choice=frontier['choices'][ci]
     if not missing or choice['kind']!='FRONTIER_EXPERIENCE' or choice['actions']!=[action] or len(choice['edges'])!=1:continue
     if frontier['frontier']['edges'][choice['edges'][0]]['source']==0:choices.append(ci)
    if missing:bindings.append({'action':action,'choice_indexes':choices})
   eligible=[row for row in bindings if len(row['choice_indexes'])==1]
   unique=discovery['result']['catalogue_current'] and discovery['state_certificate']['result']['status']=='JOINT_STATE_READY' and len(bindings)==1 and len(eligible)==1
   status='UNIQUE_UNOBSERVED_ACTION_SELECTION_READY' if unique else 'UNOBSERVED_ACTION_ALTERNATIVES_RETAINED' if bindings else 'NO_CURRENT_UNOBSERVED_ACTION'
   expected={'status':status,'selected_action':eligible[0]['action'] if unique else None,'selected_choice_index':eligible[0]['choice_indexes'][0] if unique else None,'effect_predicted':False,'separation_claimed':False}
   return canonical(certificate['coverage'])==canonical(coverage) and canonical(certificate['bindings'])==canonical(bindings) and canonical(certificate['result'])==canonical(expected)
  except (ValueError,KeyError,TypeError,IndexError,AttributeError):return False

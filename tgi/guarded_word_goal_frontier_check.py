"""Independent binding of quantified closure, route depth and actual frontier."""
from .guarded_word_closure_check import verify_guarded_word_closure
from .actuation_goal_frontier_check import verify_actuation_goal_frontier
from .frame_engine import canonical
from .role_work import RoleSearchBudget

def verify_guarded_word_goal_frontier(*args,goal,certificate,max_depth=None,max_search_steps=None):
 b=RoleSearchBudget(max_search_steps)
 with b.scope():
  try:
   b.consume();c=certificate
   if type(c) is not dict or set(c)!={'policy','goal','max_depth','effective_depth','depth_origin','closure','frontier','discovery','choices','result'} or c['policy']!='guarded_word_goal_frontier_v1' or canonical(c['goal'])!=canonical(goal) or type(max_depth) is bool or (max_depth is not None and (type(max_depth) is not int or max_depth<0)) or type(c['max_depth']) is not type(max_depth) or c['max_depth']!=max_depth:return False
   if not verify_guarded_word_closure(*args,goal=goal,certificate=c['closure']):return False
   r=c['closure']['result'];distance=r['shortest_supported_goal_length'];effective=max_depth if max_depth is not None else distance if distance is not None else 1;origin='DECLARED_SEARCH_DEPTH' if max_depth is not None else 'QUANTIFIED_SHORTEST_GOAL_BOUND' if distance is not None else 'ACTUAL_EXPERIENCE_LAYER_AFTER_CLOSURE'
   if type(c['effective_depth']) is not int or c['effective_depth']!=effective or c['depth_origin']!=origin or not verify_actuation_goal_frontier(*args,goal,c['frontier'],max_depth=effective):return False
   if canonical(c['discovery'])!=canonical(c['frontier']['discovery']) or canonical(c['closure']['discovery'])!=canonical(c['discovery']) or canonical(c['choices'])!=canonical(c['frontier']['choices']):return False
   status=c['frontier']['result']['status'] if c['frontier']['result']['status'] in ('GOAL_ALREADY_OBSERVED','SUPPORTED_GOAL_READY') else r['status'] if distance is None else c['frontier']['result']['status']
   return canonical(c['result'])==canonical({'status':status,'closure_status':r['status'],'native_frontier_status':c['frontier']['result']['status'],'choice_count':len(c['frontier']['choices']),'quantified_guarded_word_system_complete':r['quantified_guarded_word_system_complete']})
  except (ValueError,TypeError,IndexError,KeyError,AttributeError):return False

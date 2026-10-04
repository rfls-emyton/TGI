"""Quantified closure determines full-route depth; actual experience stays native."""
from copy import deepcopy
from .guarded_word_closure import certify_guarded_word_closure
from .actuation_goal_frontier import certify_actuation_goal_frontier
from .role_work import RoleSearchBudget

def certify_guarded_word_goal_frontier(*args,goal,max_depth=None,max_search_steps=None):
 b=RoleSearchBudget(max_search_steps)
 with b.scope():
  b.consume()
  if max_depth is not None and (type(max_depth) is not int or max_depth<0):raise ValueError('Original declared depth required')
  closure=certify_guarded_word_closure(*args,goal=goal);r=closure['result'];distance=r['shortest_supported_goal_length'];effective=max_depth if max_depth is not None else distance if distance is not None else 1;origin='DECLARED_SEARCH_DEPTH' if max_depth is not None else 'QUANTIFIED_SHORTEST_GOAL_BOUND' if distance is not None else 'ACTUAL_EXPERIENCE_LAYER_AFTER_CLOSURE';frontier=certify_actuation_goal_frontier(*args,goal,max_depth=effective);status=frontier['result']['status'] if frontier['result']['status'] in ('GOAL_ALREADY_OBSERVED','SUPPORTED_GOAL_READY') else r['status'] if distance is None else frontier['result']['status']
  return {'policy':'guarded_word_goal_frontier_v1','goal':deepcopy(goal),'max_depth':max_depth,'effective_depth':effective,'depth_origin':origin,'closure':closure,'frontier':frontier,'discovery':deepcopy(frontier['discovery']),'choices':deepcopy(frontier['choices']),'result':{'status':status,'closure_status':r['status'],'native_frontier_status':frontier['result']['status'],'choice_count':len(frontier['choices']),'quantified_guarded_word_system_complete':r['quantified_guarded_word_system_complete']}}

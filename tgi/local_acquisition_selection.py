"""Bind a unique native choice to complete current local acquisition evidence."""
from copy import deepcopy
from tgi.frame_engine import canonical
from tgi.role_work import RoleSearchBudget
from tgi.local_acquisition_ownership import OwnedAcquisitionContext
from tgi.unobserved_action_selection import certify_unobserved_action_selection
from tgi.unobserved_action_selection_check import verify_unobserved_action_selection
from tgi.context_family_selection import certify_context_family_selection
from tgi.context_family_selection_check import verify_context_family_selection

KINDS={'ACQUISITION':(certify_unobserved_action_selection,verify_unobserved_action_selection,'UNIQUE_UNOBSERVED_ACTION_SELECTION_READY'),'SEPARATION':(certify_context_family_selection,verify_context_family_selection,'UNIQUE_NATIVE_SEPARATOR_SELECTION_READY')}
def select_local_action(runtime,goal,kind,*,max_search_steps=None):
 b=RoleSearchBudget(max_search_steps)
 with b.scope():
  b.consume()
  if kind not in KINDS:raise ValueError('Original native choice kind required')
  args=runtime.context();frontier=OwnedAcquisitionContext(*args).frontier(goal);producer,checker,status=KINDS[kind];c=producer(*args,frontier=frontier)
  if not checker(*args,frontier=frontier,certificate=c) or c['result']['status']!=status:raise ValueError('Unique source-bound native selection required; alternatives retained')
  action=c['result']['selected_action'];index=runtime.plan()['available_actions'].index(action);row={'revision':'local_acquisition_selection_v119','kind':kind,'goal':deepcopy(goal),'frontier':frontier,'certificate':c,'action_index':index}
  if not verify_local_selection(*args,selection=row):raise ValueError('Independent complete action binding failed')
  return row

def verify_local_selection(*args,selection,max_search_steps=None):
 b=RoleSearchBudget(max_search_steps)
 with b.scope():
  b.consume()
  try:
   row=selection
   if type(row) is not dict or set(row)!={'revision','kind','goal','frontier','certificate','action_index'} or row['revision']!='local_acquisition_selection_v119' or row['kind'] not in KINDS:return False
   f=row['frontier'];c=row['certificate'];_,checker,status=KINDS[row['kind']]
   if canonical(row['goal'])!=canonical(f['goal']) or not checker(*args,frontier=f,certificate=c) or c['result']['status']!=status:return False
   index=row['action_index'];choice=c['result']['selected_choice_index'];action=c['result']['selected_action']
   return type(index) is int and 0<=index<len(f['discovery']['available_actions']) and f['discovery']['available_actions'][index]==action and type(choice) is int and 0<=choice<len(f['choices']) and f['choices'][choice]['actions']==[action]
  except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

def advance_selected(runtime,selection,*acquired,catalogue=None,catalogue_measurements=None,max_search_steps=None):
 b=RoleSearchBudget(max_search_steps)
 with b.scope():
  b.consume()
  if not verify_local_selection(*runtime.context(),selection=selection):raise ValueError('Complete original current selection required')
  return runtime.advance(selection['action_index'],*acquired,catalogue=catalogue,catalogue_measurements=catalogue_measurements)

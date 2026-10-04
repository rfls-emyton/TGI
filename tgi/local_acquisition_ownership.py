"""Own exact acquisition evidence without granting global organization authority."""
from copy import deepcopy
from types import MappingProxyType
from tgi.organization import RawOrganization
from tgi.acquisition_snapshot import acquisition_snapshot
from tgi.organization_snapshot import _Frames
from tgi.spatial import LatticeView
from tgi.role_work import RoleSearchBudget

MODEL_SLOTS=(0,3,7)

def _clone_model(engine,memo,budget):
 if id(engine) in memo:return memo[id(engine)]
 budget.consume();view=acquisition_snapshot(engine);lattice=view.frames.view()
 budget.consume_many(len(lattice.atoms)+sum(len(edges) for edges in lattice.bonds.values())+len(lattice.origins))
 for source,(frames,receipts) in view.episodes.items():
  budget.consume_many(1+len(receipts)+sum(len(frame) for frame in frames))
  if not view._alive(source):raise ValueError('Complete phase-valid original acquisition source required')
 obj=OwnedAcquisitionModel.__new__(OwnedAcquisitionModel);memo[id(engine)]=obj
 if id(engine.frames) in memo:obj.frames=memo[id(engine.frames)]
 else:
  obj.frames=_Frames(LatticeView(MappingProxyType(deepcopy(dict(lattice.atoms),memo)),MappingProxyType(deepcopy(dict(lattice.bonds),memo)),MappingProxyType(deepcopy(dict(lattice.origins),memo))));memo[id(engine.frames)]=obj.frames
 obj.episodes=MappingProxyType(deepcopy(dict(view.episodes),memo));obj.organizations=MappingProxyType({});obj.rejected_organizations=MappingProxyType({});obj._dirty=True
 return obj

class OwnedAcquisitionModel(RawOrganization):
 _acquisition_only=True
 def __init__(self,*args,**kwargs):raise TypeError('Construct through original acquisition ownership')
 def __deepcopy__(self,memo):
  budget=RoleSearchBudget()
  with budget.scope():return _clone_model(self,memo,budget)
 def observe(self,*args,**kwargs):raise TypeError('Owned acquisition evidence cannot be mutated')
 def form(self,*args,**kwargs):raise TypeError('Owned acquisition evidence has no global formation authority')
 def resolve(self,*args,**kwargs):raise TypeError('Owned acquisition evidence has no global resolution authority')
 def _phase_valid(self,*args,**kwargs):raise TypeError('Local certificates do not authorize global organization phase')
 def save(self,*args,**kwargs):raise TypeError('Persist a complete typed transaction, not a global organization model')
 @classmethod
 def load(cls,*args,**kwargs):raise TypeError('Restore complete typed evidence with its external binding')

def _own(args,budget):
 if type(args) is not tuple or len(args)!=9:raise ValueError('All nine original acquisition context objects required')
 if any(not isinstance(args[i],RawOrganization) for i in MODEL_SLOTS):raise TypeError('Original raw models required')
 if any(type(args[i]) is not list for i in (1,2,4,5,8)) or type(args[6]) is not int:raise TypeError('Original group, measurement and anchor types required')
 memo={}
 for slot in MODEL_SLOTS:_clone_model(args[slot],memo,budget)
 return deepcopy(args,memo)

class OwnedAcquisitionContext:
 """A full owned acquisition input. Knowledge requires verified local certificates."""
 def __init__(self,*args,max_search_steps=None):
  budget=RoleSearchBudget(max_search_steps)
  with budget.scope():
   budget.consume();owned=_own(args,budget)
  self._args=owned;self.ownership_work=budget.used
 def context(self,*,max_search_steps=None):
  budget=RoleSearchBudget(max_search_steps)
  with budget.scope():budget.consume();return _own(self._args,budget)
 def frontier(self,goal,*,max_depth=None,max_search_steps=None):
  from tgi.guarded_word_goal_frontier import certify_guarded_word_goal_frontier
  from tgi.guarded_word_goal_frontier_check import verify_guarded_word_goal_frontier
  budget=RoleSearchBudget(max_search_steps)
  with budget.scope():
   budget.consume();certificate=certify_guarded_word_goal_frontier(*self._args,goal=goal,max_depth=max_depth)
   if not verify_guarded_word_goal_frontier(*self._args,goal=goal,certificate=certificate,max_depth=max_depth):raise ValueError('Complete independently verified local frontier required')
   return certificate

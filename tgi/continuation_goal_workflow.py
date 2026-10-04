"""Owned catalogue-aware selection, retained actual sessions and atomic recovery."""
from copy import deepcopy
from hashlib import sha256
import json,os,re,tempfile
from pathlib import Path
from .observed_actuation_runtime import ObservedActuationRuntime,raw
from .continuation_goal_frontier import certify_continuation_goal_frontier as certify_actuation_goal_frontier
from .continuation_goal_frontier_check import verify_continuation_goal_frontier as verify_actuation_goal_frontier
from .actuation_sequence_feedback import certify_actuation_sequence_feedback
from .actuation_sequence_feedback_check import verify_actuation_sequence_feedback,same_state_context
from .organization import RawOrganization
from .organization_snapshot import snapshot
from .organization_inventory_check import verify_organization_inventory
from .identity import REGISTRY_ID
from .frame_engine import canonical,unique_object
from .role_work import RoleSearchBudget
from .incremental import FormationSearchLimit
REVISION='TGI-CONTINUATION-GOAL-WORKFLOW-V1'
FIELDS={'origin','frontier','selection_index','records','current','current_plan','current_frontier','feedback'}

def verify_session(s,goal,max_depth,budget):
    budget.consume()
    if type(s) is not dict or set(s)!=FIELDS or len(s['origin'])!=9 or len(s['current'])!=9 or type(s['records']) is not list:return False
    for args in (s['origin'],s['current']):
        if not verify_organization_inventory(snapshot(args[0])):return False
    if not verify_actuation_goal_frontier(*s['origin'],goal=goal,certificate=s['frontier'],max_depth=max_depth) or not verify_actuation_goal_frontier(*s['current'],goal=goal,certificate=s['current_frontier'],max_depth=max_depth):return False
    if canonical(s['current_frontier']['discovery'])!=canonical(s['current_plan']):return False
    if s['selection_index'] is None:return not s['records'] and s['feedback'] is None and same_state_context(s['origin'],s['current'],budget)
    return verify_actuation_sequence_feedback(s['origin'],goal,s['frontier']['frontier'],s['selection_index'],s['records'],s['current'],s['current_plan'],s['feedback'],max_depth=s['frontier']['effective_depth'])

def verify_sessions(archived,active,goal,max_depth,budget):
    if type(archived) is not list:return False
    previous=None
    for s in [*archived,active]:
        if not verify_session(s,goal,max_depth,budget) or (previous is not None and not same_state_context(previous,s['origin'],budget)):return False
        previous=s['current']
    return True

class ContinuationGoalWorkflow:
    def __init__(self,runtime,goal,*,max_depth=None,max_search_steps=None):
        b=RoleSearchBudget(max_search_steps)
        with b.scope():
            b.consume();self._runtime=deepcopy(runtime);self._goal=deepcopy(goal);self._depth=max_depth;args=self._runtime.context();frontier=certify_actuation_goal_frontier(*args,goal=goal,max_depth=max_depth)
            self._active={'origin':args,'frontier':frontier,'selection_index':None,'records':[],'current':deepcopy(args),'current_plan':self._runtime.plan(),'current_frontier':deepcopy(frontier),'feedback':None};self._archived=[]
            if not verify_sessions(self._archived,self._active,self._goal,self._depth,b):raise ValueError('Verified complete native goal workflow required')
    def frontier(self):return deepcopy(self._active['current_frontier'])
    def feedback(self):return deepcopy(self._active['feedback'])
    def runtime(self):return deepcopy(self._runtime)
    def sessions(self):return deepcopy([*self._archived,self._active])
    def select(self,index,*,max_search_steps=None):
        b=RoleSearchBudget(max_search_steps)
        with b.scope():
            b.consume()
            if self._active['selection_index'] is not None or self._active['records']:raise ValueError('Replan before selecting another complete sequence')
            obj=self.replan() if canonical(self._active['frontier'])!=canonical(self._active['current_frontier']) else deepcopy(self);obj._active['selection_index']=index;obj._active['feedback']=certify_actuation_sequence_feedback(obj._active['origin'],obj._goal,obj._active['frontier']['frontier'],index,[],obj._active['current'],obj._active['current_plan'],max_depth=obj._active['frontier']['effective_depth'])
            if not verify_sessions(obj._archived,obj._active,obj._goal,obj._depth,b):raise ValueError('Independent selected workflow verification failed')
            return obj
    def pending(self):
        s=self._active
        if s['selection_index'] is None:return {'status':'SELECTION_REQUIRED','action':None,'position':0}
        f=s['feedback']['result'];position=f['consumed_steps']
        if f['terminal']:return {'status':f['status'],'action':None,'position':position}
        choice=s['frontier']['choices'][s['selection_index']];action=choice['actions'][position];p=s['current_plan']
        status='FRESH_CATALOGUE_REQUIRED' if not p['result']['catalogue_current'] else 'PLANNED_ACTION_UNAVAILABLE' if action not in p['available_actions'] else 'ACTUAL_TRANSITION_READY'
        return {'status':status,'action':action,'position':position}
    def _renew(self,runtime):
        obj=deepcopy(self);obj._runtime=runtime;obj._active['current']=runtime.context();obj._active['current_plan']=runtime.plan();obj._active['current_frontier']=certify_actuation_goal_frontier(*obj._active['current'],goal=obj._goal,max_depth=obj._depth)
        if obj._active['selection_index'] is not None:obj._active['feedback']=certify_actuation_sequence_feedback(obj._active['origin'],obj._goal,obj._active['frontier']['frontier'],obj._active['selection_index'],obj._active['records'],obj._active['current'],obj._active['current_plan'],max_depth=obj._active['frontier']['effective_depth'])
        return obj
    def advance(self,acquired,groups,measurements,group_index,*,catalogue=None,catalogue_measurements=None,max_search_steps=None):
        b=RoleSearchBudget(max_search_steps)
        with b.scope():
            b.consume();pending=self.pending()
            if pending['status']!='ACTUAL_TRANSITION_READY':raise ValueError('Selected, available, current nonterminal action required')
            args=self._runtime.context();p=self._runtime.plan();index=p['available_actions'].index(pending['action']);context=(*args,p,index,acquired,groups,measurements,group_index);next,c=self._runtime.advance(index,acquired,groups,measurements,group_index,catalogue=catalogue,catalogue_measurements=catalogue_measurements)
            if next is None:return None,c
            obj=deepcopy(self);obj._active['records'].append(deepcopy({'context':context,'after':next.context()[0],'certificate':c}));obj=obj._renew(next)
            if not verify_sessions(obj._archived,obj._active,obj._goal,obj._depth,b):raise ValueError('Independent actual workflow verification failed')
            return obj,c
    def refresh_catalogue(self,catalogue,measurements,*,max_search_steps=None):
        b=RoleSearchBudget(max_search_steps)
        with b.scope():
            b.consume();obj=self._renew(self._runtime.refresh_catalogue(catalogue,measurements))
            if not verify_sessions(obj._archived,obj._active,obj._goal,obj._depth,b):raise ValueError('Independent catalogue refresh verification failed')
            return obj
    def replan(self,*,max_search_steps=None):
        b=RoleSearchBudget(max_search_steps)
        with b.scope():
            b.consume();obj=type(self)(self._runtime,self._goal,max_depth=self._depth);obj._archived=deepcopy([*self._archived,self._active])
            if not verify_sessions(obj._archived,obj._active,obj._goal,obj._depth,b):raise ValueError('Independent retained session verification failed')
            return obj
    def commit(self,path,*,max_search_steps=None):
        b=RoleSearchBudget(max_search_steps)
        with b.scope():
            b.consume();archived,active=deepcopy((self._archived,self._active))
            if not verify_sessions(archived,active,self._goal,self._depth,b):raise ValueError('Complete independently verified workflow required')
            models=[];known={}
            def model_id(m):
                rows=raw(m);key=canonical(rows);b.consume_many(sum(len(f) for row in rows for f in row['frames'])+1)
                if key not in known:known[key]=len(models);models.append(rows)
                return {'model':known[key]}
            def context(args):return [model_id(v) if i in ((0,3,7) if len(args)==9 else (0,3,7,11)) else v for i,v in enumerate(args)]
            def session(s):return {**s,'origin':context(s['origin']),'current':context(s['current']),'records':[{'context':context(r['context']),'after':model_id(r['after']),'certificate':r['certificate']} for r in s['records']]}
            saved_archived=[session(s) for s in archived];saved_active=session(active);payload={'revision':REVISION,'registry':REGISTRY_ID,'goal':deepcopy(self._goal),'max_depth':self._depth,'root_origin':context((archived[0] if archived else active)['origin']),'models':models,'archived':saved_archived,'active':saved_active};data=canonical({'payload':payload,'sha256':sha256(canonical(payload).encode()).hexdigest()}).encode('utf8');path=Path(path);temporary=None
            try:
                with tempfile.NamedTemporaryFile(mode='wb',prefix='tgi-goal-',dir=path.parent,delete=False) as f:temporary=Path(f.name);f.write(data);f.flush();os.fsync(f.fileno())
                os.replace(temporary,path);temporary=None
            finally:
                if temporary is not None and temporary.exists():temporary.unlink()
            return {'path':str(path),'sha256':sha256(data).hexdigest(),'bytes':len(data),'revision':REVISION,'raw_inventory_models':len(models),'archived_sessions':len(archived),'actual_records':sum(len(s['records']) for s in [*archived,active])}
    @classmethod
    def recover(cls,path,expected_sha256,*,max_search_steps=None):
        b=RoleSearchBudget(max_search_steps)
        with b.scope():
            b.consume();data=Path(path).read_bytes()
            if not isinstance(expected_sha256,str) or re.fullmatch('[0-9a-f]{64}',expected_sha256) is None or sha256(data).hexdigest()!=expected_sha256:raise ValueError('Original external workflow byte digest required')
            envelope=json.loads(data.decode('utf8'),object_pairs_hook=unique_object)
            if type(envelope) is not dict or set(envelope)!={'payload','sha256'}:raise ValueError('Invalid workflow envelope')
            p=envelope['payload']
            if type(p) is not dict or set(p)!={'revision','registry','goal','max_depth','root_origin','models','archived','active'} or p['revision']!=REVISION or p['registry']!=REGISTRY_ID or sha256(canonical(p).encode()).hexdigest()!=envelope['sha256']:raise ValueError('Invalid complete workflow payload')
            if type(p['models']) is not list or not p['models']:raise ValueError('Original raw inventory pool required')
            models=[];unique=set()
            for rows in p['models']:
                if type(rows) is not list or canonical(rows) in unique:raise ValueError('Unique complete raw inventory pool required')
                unique.add(canonical(rows));m=RawOrganization()
                for row in rows:
                    if type(row) is not dict or set(row)!={'source','frames'} or type(row['frames']) is not list:raise ValueError('Original raw episode required')
                    b.consume_many(sum(len(f) for f in row['frames'])+1);m.observe(row['source'],row['frames'])
                limits=[];parent=b
                while parent is not None:
                    if parent.limit is not None:limits.append(max(0,parent.limit-parent.used))
                    parent=getattr(parent,'parent',None)
                try:m.form(max_search_steps=min(limits) if limits else None)
                except FormationSearchLimit as error:b.consume_many(error.used);b.consume();raise
                b.consume_many(m.formation_work['search_steps']);models.append(m)
            used=set()
            def model(marker):
                if type(marker) is not dict or set(marker)!={'model'} or type(marker['model']) is not int or not 0<=marker['model']<len(models):raise ValueError('Exact original model slot required')
                used.add(marker['model']);return models[marker['model']]
            def context(args,size):
                if type(args) is not list or len(args)!=size:raise ValueError('Complete original model context required')
                for i in ((0,3,7) if size==9 else (0,3,7,11)):args[i]=model(args[i])
                return tuple(args)
            def session(s):
                if type(s) is not dict or set(s)!=FIELDS or type(s['records']) is not list:raise ValueError('Complete original session required')
                s['origin']=context(s['origin'],9);s['current']=context(s['current'],9)
                for r in s['records']:
                    if type(r) is not dict or set(r)!={'context','after','certificate'}:raise ValueError('Complete original actual transition required')
                    r['context']=context(r['context'],15);r['after']=model(r['after'])
                return s
            if type(p['archived']) is not list:raise ValueError('Ordered retained sessions required')
            archived=[session(s) for s in p['archived']];active=session(p['active']);root_origin=context(p['root_origin'],9)
            first=(archived[0] if archived else active)['origin']
            if not same_state_context(root_origin,first,b) or canonical(root_origin[8])!=canonical(first[8]) or canonical(raw(root_origin[7]))!=canonical(raw(first[7])):raise ValueError('Original root session binding required')
            if used!=set(range(len(models))) or not verify_sessions(archived,active,p['goal'],p['max_depth'],b):raise ValueError('Independent full workflow recovery verification failed')
            obj=cls.__new__(cls);obj._goal=p['goal'];obj._depth=p['max_depth'];obj._archived=archived;obj._active=active;runtime=ObservedActuationRuntime.__new__(ObservedActuationRuntime);runtime._args=tuple(active['current']);runtime._plan=active['current_plan'];runtime._transaction=None
            for s in [*archived,active]:
                for r in s['records']:runtime._transaction=(tuple(r['context']),r['after'],r['certificate'])
            obj._runtime=runtime;return obj

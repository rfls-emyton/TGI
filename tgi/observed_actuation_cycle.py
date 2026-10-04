"""Neutral owned API and atomic full transaction persistence for discovery."""
from copy import deepcopy
from hashlib import sha256
import json,os,re,tempfile
from pathlib import Path
from .observed_actuation_discovery import certify_observed_actuation_discovery
from .observed_actuation_discovery_check import verify_observed_actuation_discovery
from .observed_actuation_learning import prepare_observed_actuation_learning
from .observed_actuation_learning_check import verify_observed_actuation_learning
from .acquisition_snapshot import acquisition_snapshot
from .organization_snapshot import snapshot
from .organization_inventory_check import verify_organization_inventory
from .organization import RawOrganization
from .identity import decode,REGISTRY_ID
from .frame_engine import canonical,unique_object
from .role_work import RoleSearchBudget
from .incremental import FormationSearchLimit

REVISION='TGI-OBSERVED-ACTUATION-CHECKPOINT-V1'
PARENT_SLOTS=(0,3,7,11)
CURRENT_SLOTS=(0,3,7)

def raw(model):
    return [{'source':s,'frames':list(map(decode,frames))} for s,(frames,_) in acquisition_snapshot(model).episodes.items()]


def verify_successor(context,after,certificate,current,plan,budget):
    budget.consume()
    if len(context)!=15 or len(current)!=9 or not verify_observed_actuation_learning(*context,after,certificate) or not certificate['result']['experience_admitted']:return False
    h=certificate['history'];anchor=h.get('acquired_group_indices',list(range(len(context[1]),len(context[1])+len(context[12]))))[context[14]]
    if raw(current[0])!=raw(after) or raw(current[3])!=raw(after):return False
    if canonical([current[1],current[2],current[4],current[5],current[6]])!=canonical([h['groups'],h['measurements'],h['groups'],h['measurements'],anchor]):return False
    return verify_organization_inventory(snapshot(current[0])) and verify_organization_inventory(snapshot(current[3])) and verify_observed_actuation_discovery(*current,plan)


class ObservedActuationCycle:
    def __init__(self,model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,catalogue,catalogue_measurements,*,max_search_steps=None):
        budget=RoleSearchBudget(max_search_steps)
        with budget.scope():
            budget.consume();self._args=deepcopy((model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,catalogue,catalogue_measurements))
            if not verify_organization_inventory(snapshot(self._args[0])):raise ValueError('Verified original knowledge inventory required')
            self._plan=certify_observed_actuation_discovery(*self._args)
            if not verify_observed_actuation_discovery(*self._args,self._plan):raise ValueError('Independent discovery verification failed')
            self._transaction=None

    @property
    def status(self):return self._plan['result']['status']

    def context(self):return deepcopy(self._args)
    def plan(self):return deepcopy(self._plan)

    def learn(self,request_index,acquired,groups,measurements,group_index,*,catalogue=None,catalogue_measurements=None,max_search_steps=None):
        budget=RoleSearchBudget(max_search_steps)
        with budget.scope():
            budget.consume()
            if (catalogue is None)!=(catalogue_measurements is None):raise ValueError('Catalogue and measurements supplied together')
            context=(*self._args,self._plan,request_index,acquired,groups,measurements,group_index);after,c=prepare_observed_actuation_learning(*context)
            if not verify_observed_actuation_learning(*context,after,c):raise ValueError('Independent acquired learning verification failed')
            if not c['result']['experience_admitted']:return None,c
            h=c['history'];cat,cm=(self._args[7],self._args[8]) if catalogue is None else (catalogue,catalogue_measurements);successor=type(self)(after,h['groups'],h['measurements'],after,h['groups'],h['measurements'],h.get('acquired_group_indices',list(range(len(self._args[1]),len(self._args[1])+len(groups))))[group_index],cat,cm);successor._transaction=deepcopy((context,after,c));return successor,c

    def refresh_catalogue(self,catalogue,measurements,*,max_search_steps=None):
        obj=type(self)(*self._args[:7],catalogue,measurements,max_search_steps=max_search_steps);obj._transaction=deepcopy(self._transaction);return obj

    def commit(self,path,*,max_search_steps=None):
        budget=RoleSearchBudget(max_search_steps)
        with budget.scope():
            budget.consume()
            if self._transaction is None:raise ValueError('Admitted discovery transaction required')
            context,after,c=deepcopy(self._transaction);current=deepcopy(self._args);plan=deepcopy(self._plan)
            if not verify_successor(context,after,c,current,plan,budget):raise ValueError('Verified complete discovery successor required')
            models=[raw(context[i]) for i in PARENT_SLOTS]+[raw(after)]+[raw(current[i]) for i in CURRENT_SLOTS];parent=[{'model':PARENT_SLOTS.index(i)} if i in PARENT_SLOTS else x for i,x in enumerate(context)];args=[{'model':5+CURRENT_SLOTS.index(i)} if i in CURRENT_SLOTS else x for i,x in enumerate(current)];payload={'revision':REVISION,'registry':REGISTRY_ID,'models':models,'context':parent,'certificate':c,'current':args,'plan':plan};data=canonical({'payload':payload,'sha256':sha256(canonical(payload).encode()).hexdigest()}).encode('utf8');path=Path(path);temporary=None
            try:
                with tempfile.NamedTemporaryFile(mode='wb',dir=path.parent,delete=False) as stream:temporary=Path(stream.name);stream.write(data);stream.flush();os.fsync(stream.fileno())
                os.replace(temporary,path);temporary=None
            finally:
                if temporary is not None and temporary.exists():temporary.unlink()
            return {'path':str(path),'sha256':sha256(data).hexdigest(),'bytes':len(data),'revision':REVISION}

    @classmethod
    def recover(cls,path,expected_sha256,*,max_search_steps=None):
        budget=RoleSearchBudget(max_search_steps)
        with budget.scope():
            budget.consume()
            if not isinstance(expected_sha256,str) or re.fullmatch('[0-9a-f]{64}',expected_sha256) is None:raise ValueError('Original external file digest required')
            data=Path(path).read_bytes()
            if sha256(data).hexdigest()!=expected_sha256:raise ValueError('Original checkpoint digest mismatch')
            e=json.loads(data.decode('utf8'),object_pairs_hook=unique_object)
            if type(e) is not dict or set(e)!={'payload','sha256'}:raise ValueError('Invalid discovery envelope')
            p=e['payload']
            if type(p) is not dict or set(p)!={'revision','registry','models','context','certificate','current','plan'} or p['revision']!=REVISION or p['registry']!=REGISTRY_ID or sha256(canonical(p).encode()).hexdigest()!=e['sha256']:raise ValueError('Invalid discovery payload')
            if type(p['models']) is not list or len(p['models'])!=8 or type(p['context']) is not list or len(p['context'])!=15 or type(p['current']) is not list or len(p['current'])!=9:raise ValueError('Complete discovery transaction required')
            models=[]
            for rows in p['models']:
                if type(rows) is not list:raise ValueError('Ordered original raw episodes required')
                model=RawOrganization()
                for row in rows:
                    if type(row) is not dict or set(row)!={'source','frames'} or type(row['frames']) is not list:raise ValueError('Invalid raw episode')
                    budget.consume_many(sum(len(f) for f in row['frames'])+1);model.observe(row['source'],row['frames'])
                current_budget=budget;limits=[]
                while current_budget is not None:
                    if current_budget.limit is not None:limits.append(max(0,current_budget.limit-current_budget.used))
                    current_budget=getattr(current_budget,'parent',None)
                try:model.form(max_search_steps=min(limits) if limits else None)
                except FormationSearchLimit as error:budget.consume_many(error.used);budget.consume();raise
                budget.consume_many(model.formation_work['search_steps']);models.append(model)
            context=p['context'];args=p['current']
            for slots,target,offset in [(PARENT_SLOTS,context,0),(CURRENT_SLOTS,args,5)]:
                for index,slot in enumerate(slots):
                    marker=target[slot]
                    if type(marker) is not dict or set(marker)!={'model'} or type(marker['model']) is not int or marker['model']!=offset+index:raise ValueError('Original model slot required')
                    target[slot]=models[offset+index]
            if not verify_successor(context,models[4],p['certificate'],args,p['plan'],budget):raise ValueError('Native discovery checkpoint verification failed')
            obj=cls.__new__(cls);obj._args=tuple(args);obj._plan=p['plan'];obj._transaction=(tuple(context),models[4],p['certificate']);return obj

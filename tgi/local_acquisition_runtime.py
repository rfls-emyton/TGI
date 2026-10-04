from tgi.local_evidence_persistence import ENCODING,pack,unpack
from tgi.local_acquisition_ownership import OwnedAcquisitionContext,OwnedAcquisitionModel,_clone_model
"""Owned available-action runtime and atomic complete transition persistence."""
from copy import deepcopy
from hashlib import sha256
import json,os,re,tempfile
from pathlib import Path
from tgi.observed_actuation_discovery import certify_observed_actuation_discovery
from tgi.observed_actuation_discovery_check import verify_observed_actuation_discovery
from tgi.local_acquisition_transition import prepare_measured_actuation_transition
from tgi.local_acquisition_transition_check import verify_measured_actuation_transition
from tgi.acquisition_snapshot import acquisition_snapshot
from tgi.organization import RawOrganization
from tgi.identity import decode,REGISTRY_ID
from tgi.frame_engine import canonical,unique_object
from tgi.role_work import RoleSearchBudget
from tgi.incremental import FormationSearchLimit

REVISION='TGI-LOCAL-ACQUISITION-RUNTIME-CHECKPOINT-V119-GRAPH-V2'
PARENT_SLOTS=(0,3,7,11)
CURRENT_SLOTS=(0,3,7)

def raw(model):
    return [{'source':s,'frames':list(map(decode,frames))} for s,(frames,_) in acquisition_snapshot(model).episodes.items()]


def verify_successor(context,after,certificate,current,plan,budget):
    budget.consume()
    if len(context)!=15 or len(current)!=9 or not verify_measured_actuation_transition(*context,after,certificate) or not certificate['result']['experience_admitted']:return False
    h=certificate['history'];anchor=h.get('acquired_group_indices',list(range(len(context[1]),len(context[1])+len(context[12]))))[context[14]]
    if raw(current[0])!=raw(after) or raw(current[3])!=raw(after):return False
    if canonical([current[1],current[2],current[4],current[5],current[6]])!=canonical([h['groups'],h['measurements'],h['groups'],h['measurements'],anchor]):return False
    return all(isinstance(current[i],OwnedAcquisitionModel) for i in CURRENT_SLOTS) and verify_observed_actuation_discovery(*current,plan)


class LocalAcquisitionRuntime:
    def __init__(self,model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,catalogue,catalogue_measurements,*,max_search_steps=None):
        budget=RoleSearchBudget(max_search_steps)
        with budget.scope():
            budget.consume();self._args=OwnedAcquisitionContext(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,catalogue,catalogue_measurements).context()
            self._plan=certify_observed_actuation_discovery(*self._args)
            if not verify_observed_actuation_discovery(*self._args,self._plan):raise ValueError('Independent discovery verification failed')
            self._transaction=None

    @property
    def status(self):return self._plan['result']['status']

    def context(self):return deepcopy(self._args)
    def plan(self):return deepcopy(self._plan)

    def advance(self,action_index,acquired,groups,measurements,group_index,*,catalogue=None,catalogue_measurements=None,max_search_steps=None):
        budget=RoleSearchBudget(max_search_steps)
        with budget.scope():
            budget.consume()
            if (catalogue is None)!=(catalogue_measurements is None):raise ValueError('Catalogue and measurements supplied together')
            context=(*self._args,self._plan,action_index,acquired,groups,measurements,group_index);after,c=prepare_measured_actuation_transition(*context)
            if not verify_measured_actuation_transition(*context,after,c):raise ValueError('Independent acquired learning verification failed')
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
            model_objects=[context[i] for i in PARENT_SLOTS]+[after]+[current[i] for i in CURRENT_SLOTS];models=[];frames=[];model_ids={};frame_ids={}
            for model in model_objects:
                if id(model) in model_ids:continue
                if id(model.frames) not in frame_ids:frame_ids[id(model.frames)]=len(frames);frames.append(model.frames.view())
                model_ids[id(model)]=len(models);models.append({'frame':frame_ids[id(model.frames)],'episodes':model.episodes})
            parent=[{'model':model_ids[id(context[i])]} if i in PARENT_SLOTS else x for i,x in enumerate(context)];args=[{'model':model_ids[id(current[i])]} if i in CURRENT_SLOTS else x for i,x in enumerate(current)];payload={'revision':REVISION,'registry':REGISTRY_ID,'frames':frames,'models':models,'after':{'model':model_ids[id(after)]},'context':parent,'certificate':c,'current':args,'plan':plan};encoded=pack(payload,budget);data=json.dumps({'encoding':ENCODING,'payload':encoded,'sha256':sha256(canonical(encoded).encode()).hexdigest()},ensure_ascii=True,separators=(',',':'),allow_nan=False).encode('utf8');path=Path(path);temporary=None
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
            if type(e) is not dict or set(e)!={'encoding','payload','sha256'} or e['encoding']!=ENCODING:raise ValueError('Invalid discovery envelope')
            p=unpack(e['payload'],budget)
            if type(p) is not dict or set(p)!={'revision','registry','frames','models','after','context','certificate','current','plan'} or p['revision']!=REVISION or p['registry']!=REGISTRY_ID or sha256(canonical(e['payload']).encode()).hexdigest()!=e['sha256']:raise ValueError('Invalid discovery payload')
            if type(p['models']) is not list or not 1<=len(p['models'])<=8 or type(p['frames']) is not list or not 1<=len(p['frames'])<=8 or type(p['context']) is not list or len(p['context'])!=15 or type(p['current']) is not list or len(p['current'])!=9:raise ValueError('Complete original ownership graph required')
            from tgi.organization_snapshot import _Frames
            from tgi.spatial import LatticeView
            from types import MappingProxyType
            wrappers=[]
            for view in p['frames']:
                if type(view) is not LatticeView or any(type(value) is not MappingProxyType for value in (view.atoms,view.bonds,view.origins)):raise ValueError('Complete immutable original lattice required')
                wrappers.append(_Frames(view))
            raw_models=[]
            for row in p['models']:
                if type(row) is not dict or set(row)!={'frame','episodes'} or type(row['frame']) is not int or not 0<=row['frame']<len(wrappers) or type(row['episodes']) not in (dict,MappingProxyType):raise ValueError('Original owned model record required')
                model=OwnedAcquisitionModel.__new__(OwnedAcquisitionModel);model.frames=wrappers[row['frame']];model.episodes=row['episodes'] if type(row['episodes']) is MappingProxyType else MappingProxyType(row['episodes']);model.organizations=MappingProxyType({});model.rejected_organizations=MappingProxyType({});model._dirty=True;raw_models.append(model)
            memo={};models=[_clone_model(model,memo,budget) for model in raw_models];context=p['context'];args=p['current'];used=set()
            for slots,target in [(PARENT_SLOTS,context),(CURRENT_SLOTS,args)]:
                for slot in slots:
                    marker=target[slot]
                    if type(marker) is not dict or set(marker)!={'model'} or type(marker['model']) is not int or not 0<=marker['model']<len(models):raise ValueError('Original owned model reference required')
                    used.add(marker['model']);target[slot]=models[marker['model']]
            marker=p['after']
            if type(marker) is not dict or set(marker)!={'model'} or type(marker['model']) is not int or not 0<=marker['model']<len(models):raise ValueError('Original successor model reference required')
            used.add(marker['model']);after=models[marker['model']]
            if used!=set(range(len(models))) or {row['frame'] for row in p['models']}!=set(range(len(wrappers))):raise ValueError('No omitted or fabricated ownership graph entries allowed')
            if not verify_successor(context,after,p['certificate'],args,p['plan'],budget):raise ValueError('Native discovery checkpoint verification failed')
            obj=cls.__new__(cls);obj._args=tuple(args);obj._plan=p['plan'];obj._transaction=(tuple(context),after,p['certificate']);return obj

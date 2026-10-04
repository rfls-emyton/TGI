"""Neutral atomic persistence of the complete independently verified native transaction."""
from copy import deepcopy
from hashlib import sha256
import json,os,re,tempfile
from pathlib import Path
from .organization import RawOrganization
from .organization_snapshot import snapshot
from .identity import decode,REGISTRY_ID
from .frame_engine import canonical,unique_object
from .continuation_learning_check import verify_continuation_learning
from .role_work import RoleSearchBudget
from .incremental import FormationSearchLimit

REVISION='TGI-CONTINUATION-CHECKPOINT-V1'
SLOTS=(0,6,11)


def _raw(model):
    return [{'source':s,'frames':list(map(decode,frames))} for s,(frames,_) in snapshot(model).episodes.items()]


def save_continuation_checkpoint(path,context,after,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        if type(context) not in (tuple,list) or len(context)!=16:raise ValueError('Complete original continuation context required')
        if after is None:raise ValueError('Verified admitted learned state required')
        context=tuple(snapshot(x) if i in SLOTS else deepcopy(x) for i,x in enumerate(context));after=snapshot(after);certificate=deepcopy(certificate)
        if not verify_continuation_learning(*context,after,certificate) or not certificate['result']['experience_admitted']:raise ValueError('Verified admitted learned state required')
        args=[{'model':SLOTS.index(i)} if i in SLOTS else deepcopy(x) for i,x in enumerate(context)]
        payload={'revision':REVISION,'registry':REGISTRY_ID,'models':[_raw(context[i]) for i in SLOTS]+[_raw(after)],'context':args,'certificate':deepcopy(certificate)}
        envelope={'payload':payload,'sha256':sha256(canonical(payload).encode('utf8')).hexdigest()};data=canonical(envelope).encode('utf8');path=Path(path);temporary=None
        try:
            with tempfile.NamedTemporaryFile(mode='wb',dir=path.parent,delete=False) as stream:
                temporary=Path(stream.name);stream.write(data);stream.flush();os.fsync(stream.fileno())
            os.replace(temporary,path);temporary=None
        finally:
            if temporary is not None and temporary.exists():temporary.unlink()
        return {'path':str(path),'sha256':sha256(data).hexdigest(),'bytes':len(data),'revision':REVISION}


def load_continuation_checkpoint(path,expected_sha256,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        if not isinstance(expected_sha256,str) or re.fullmatch('[0-9a-f]{64}',expected_sha256) is None:raise ValueError('Original external file SHA256 required')
        data=Path(path).read_bytes()
        if sha256(data).hexdigest()!=expected_sha256:raise ValueError('Original checkpoint digest mismatch')
        e=json.loads(data.decode('utf8'),object_pairs_hook=unique_object)
        if type(e) is not dict or set(e)!={'payload','sha256'}:raise ValueError('Invalid checkpoint envelope')
        p=e['payload']
        if type(p) is not dict or set(p)!={'revision','registry','models','context','certificate'} or p['revision']!=REVISION or p['registry']!=REGISTRY_ID or sha256(canonical(p).encode('utf8')).hexdigest()!=e['sha256']:raise ValueError('Invalid checkpoint payload')
        if type(p['models']) is not list or len(p['models'])!=4 or type(p['context']) is not list or len(p['context'])!=16:raise ValueError('Complete original model context required')
        models=[]
        for rows in p['models']:
            if type(rows) is not list:raise ValueError('Original ordered raw model episodes required')
            model=RawOrganization()
            for row in rows:
                if type(row) is not dict or set(row)!={'source','frames'} or type(row['frames']) is not list:raise ValueError('Invalid raw episode')
                budget.consume_many(sum(len(f) for f in row['frames'])+1);model.observe(row['source'],row['frames'])
            limits=[];current=budget
            while current is not None:
                if current.limit is not None:limits.append(current.limit-current.used)
                current=getattr(current,'parent',None)
            try:model.form(max_search_steps=min(limits) if limits else None)
            except FormationSearchLimit as error:
                budget.consume_many(error.used);budget.consume();raise
            budget.consume_many(model.formation_work['search_steps']);models.append(model)
        context=p['context']
        for index,i in enumerate(SLOTS):
            if type(context[i]) is not dict or set(context[i])!={'model'} or type(context[i]['model']) is not int or context[i]['model']!=index:raise ValueError('Original model slot required')
            context[i]=models[index]
        certificate=p['certificate']
        if not verify_continuation_learning(*context,models[3],certificate) or not certificate['result']['experience_admitted']:raise ValueError('Checkpoint native transaction verification failed')
        return tuple(context),models[3],certificate

"""Atomic, native incremental lifecycle for source-owned spatial action relations."""
import hashlib,json,os,re,tempfile
from pathlib import Path
from .frame_engine import canonical,unique_object
from .identity import decode,REGISTRY_ID
from .organization import RawOrganization
from .organization_inventory_check import verify_organization_inventory
from .spatial_action_relation import form_relations
from .spatial_action_relation_check import verify_relations

REVISION='TGI-SPATIAL-ACTION-RELATION-CYCLE-INCREMENTAL-V2'

def sha(data):return hashlib.sha256(data).hexdigest()

def _fork_organization(parent):
    """Private successor maps; frozen atoms, bonds and receipts retain identity."""
    if type(parent) is not RawOrganization or parent._dirty or parent.frames._pending:
        raise ValueError('Complete source organization required')
    child=RawOrganization()
    for name in ('_atoms','_bonds','_origins','_contexts','_sources','_pending'):
        setattr(child.frames,name,dict(getattr(parent.frames,name)))
    child.episodes=dict(parent.episodes)
    child.organizations=dict(parent.organizations)
    child.rejected_organizations=dict(parent.rejected_organizations)
    child._dirty=False
    # StructuralCache.stage builds a new cache; it never mutates this parent.
    child._formation_cache=parent._formation_cache
    child.formation_work=dict(parent.formation_work)
    return child
def rows(model):
    return [{'source':source,'frames':[decode(frame) for frame in frames]} for source,(frames,_) in model.episodes.items()]

class SpatialRelationCycle:
    def __init__(self,model,actions,*,max_search_steps=100000):
        if type(actions) is not list or model._dirty or not verify_organization_inventory(model,max_search_steps=max_search_steps):raise ValueError('Complete native organization required')
        certificate=form_relations(model,actions,max_search_steps=max_search_steps)
        if not verify_relations(model,actions,certificate):raise ValueError('Independent relation verification failed')
        self.model=model
        self.actions=json.loads(json.dumps(actions))
        self.certificate=certificate
        self.max_search_steps=max_search_steps
    def observe(self,source,frames,action,port):
        if not verify_relations(self.model,self.actions,self.certificate):raise ValueError('Relation changed before append')
        candidate=_fork_organization(self.model)
        candidate.observe(source,frames)
        candidate.form(max_search_steps=self.max_search_steps)
        successor=type(self)(candidate,self.actions+[{'source':source,'action':action,'port':port}],max_search_steps=self.max_search_steps)
        return successor
    def commit(self,path):
        if not verify_relations(self.model,self.actions,self.certificate):raise ValueError('Relation changed before commit')
        payload={'revision':REVISION,'registry':REGISTRY_ID,'raw_episodes':rows(self.model),
                 'actions':self.actions,'certificate':self.certificate}
        envelope={'payload':payload,'sha256':sha(canonical(payload).encode('utf8'))}
        data=canonical(envelope).encode('utf8');path=Path(path);temporary=None
        try:
            with tempfile.NamedTemporaryFile(mode='wb',dir=path.parent,delete=False) as stream:
                temporary=Path(stream.name);stream.write(data);stream.flush();os.fsync(stream.fileno())
            os.replace(temporary,path);temporary=None
        finally:
            if temporary is not None and temporary.exists():temporary.unlink()
        return {'path':str(path),'sha256':sha(data),'bytes':len(data)}
    @classmethod
    def recover(cls,path,expected_sha256,*,max_search_steps=100000):
        if type(expected_sha256) is not str or re.fullmatch('[0-9a-f]{64}',expected_sha256) is None:raise ValueError('External checkpoint digest required')
        data=Path(path).read_bytes()
        if sha(data)!=expected_sha256:raise ValueError('Checkpoint digest mismatch')
        envelope=json.loads(data.decode('utf8'),object_pairs_hook=unique_object)
        if type(envelope) is not dict or set(envelope)!={'payload','sha256'}:raise ValueError('Invalid relation envelope')
        payload=envelope['payload']
        if type(payload) is not dict or set(payload)!={'revision','registry','raw_episodes','actions','certificate'} or payload['revision']!=REVISION or payload['registry']!=REGISTRY_ID or sha(canonical(payload).encode('utf8'))!=envelope['sha256']:
            raise ValueError('Invalid relation payload')
        if type(payload['raw_episodes']) is not list or type(payload['actions']) is not list:raise ValueError('Original ordered sources required')
        model=RawOrganization()
        for row in payload['raw_episodes']:
            if type(row) is not dict or set(row)!={'source','frames'}:raise ValueError('Original raw episode required')
            model.observe(row['source'],row['frames'])
        model.form(max_search_steps=max_search_steps)
        successor=cls(model,payload['actions'],max_search_steps=max_search_steps)
        if canonical(successor.certificate)!=canonical(payload['certificate']):raise ValueError('Recomputed relation mismatch')
        return successor





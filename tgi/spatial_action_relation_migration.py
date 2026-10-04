"""Research-only explicit migration of the pre-incremental spatial cycle."""
import hashlib,json,os,re,tempfile
from pathlib import Path
from .frame_engine import canonical,unique_object
from .identity import REGISTRY_ID
from .organization import RawOrganization
from .spatial_action_relation_cycle import SpatialRelationCycle,REVISION
LEGACY='TGI-SPATIAL-ACTION-RELATION-CYCLE-V1'
def sha(data):return hashlib.sha256(data).hexdigest()
def migrate_legacy_cycle(source,expected_sha256,destination):
    source=Path(source);destination=Path(destination)
    if source.resolve()==destination.resolve() or destination.exists():raise ValueError('Migration destination must be new')
    if type(expected_sha256) is not str or re.fullmatch('[0-9a-f]{64}',expected_sha256) is None:raise ValueError('External legacy digest required')
    data=source.read_bytes()
    if sha(data)!=expected_sha256:raise ValueError('Legacy checkpoint digest mismatch')
    envelope=json.loads(data.decode('utf8'),object_pairs_hook=unique_object)
    if type(envelope) is not dict or set(envelope)!={'payload','sha256'}:raise ValueError('Invalid legacy envelope')
    payload=envelope['payload']
    if type(payload) is not dict or set(payload)!={'revision','registry','raw_episodes','actions','certificate'} or payload['revision']!=LEGACY or payload['registry']!=REGISTRY_ID or sha(canonical(payload).encode())!=envelope['sha256']:
        raise ValueError('Invalid legacy payload')
    if type(payload['raw_episodes']) is not list or type(payload['actions']) is not list:raise ValueError('Invalid legacy sources')
    model=RawOrganization()
    for row in payload['raw_episodes']:
        if type(row) is not dict or set(row)!={'source','frames'}:raise ValueError('Invalid legacy episode')
        model.observe(row['source'],row['frames'])
    model.form(max_search_steps=100000)
    current=SpatialRelationCycle(model,payload['actions'])
    if canonical(current.certificate)!=canonical(payload['certificate']):raise ValueError('Legacy certificate does not replay')
    if not destination.parent.is_dir():raise ValueError('Migration destination parent required')
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent,delete=False) as stream:temporary=Path(stream.name)
        saved=current.commit(temporary)
        if destination.exists():raise ValueError('Migration destination changed')
        os.rename(temporary,destination);temporary=None
    finally:
        if temporary is not None and temporary.exists():temporary.unlink()
    return {'legacy_revision':LEGACY,'current_revision':REVISION,'legacy_sha256':expected_sha256,'current_sha256':saved['sha256'],'certificate_sha256':sha(canonical(current.certificate).encode()),'source':str(source),'destination':str(destination)}




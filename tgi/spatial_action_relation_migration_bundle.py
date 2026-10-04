"""Research-only atomic bundle for explicit spatial cycle checkpoint migration."""
import hashlib,json,os,re,shutil,tempfile
from pathlib import Path
from .frame_engine import canonical,unique_object
from .identity import REGISTRY_ID
from .spatial_action_relation_cycle import SpatialRelationCycle,REVISION
from .spatial_action_relation_migration import migrate_legacy_cycle,LEGACY
FILES={'legacy.json','current.json','migration.json'}
def sha(data):return hashlib.sha256(data).hexdigest()
def write_sync(path,data):
    with path.open('wb') as stream:
        stream.write(data);stream.flush();os.fsync(stream.fileno())
def publish_migration_bundle(source,expected_sha256,bundle):
    source=Path(source);bundle=Path(bundle);parent=bundle.parent.resolve()
    if bundle.exists() or not parent.is_dir():raise ValueError('New bundle under existing directory required')
    stage=Path(tempfile.mkdtemp(prefix=bundle.name+'.stage-',dir=parent))
    if stage.resolve().parent!=parent:raise ValueError('Staging escaped bundle parent')
    published=False
    try:
        old=stage/'legacy.json';write_sync(old,source.read_bytes())
        migrated=migrate_legacy_cycle(old,expected_sha256,stage/'current.json')
        receipt={'revision':'TGI-SPATIAL-CYCLE-MIGRATION-BUNDLE-V1','legacy_revision':LEGACY,'current_revision':REVISION,
                 'legacy_sha256':expected_sha256,'current_sha256':migrated['current_sha256'],
                 'certificate_sha256':migrated['certificate_sha256'],'files':['legacy.json','current.json']}
        write_sync(stage/'migration.json',canonical(receipt).encode('utf8'))
        if bundle.resolve().parent!=parent or bundle.exists():raise ValueError('Bundle destination changed')
        os.rename(stage,bundle);published=True
        return {'bundle':str(bundle),'receipt_sha256':sha((bundle/'migration.json').read_bytes()),**receipt}
    finally:
        if not published and stage.exists():
            if stage.resolve().parent!=parent:raise ValueError('Unsafe staging cleanup target')
            shutil.rmtree(stage)
def recover_migration_bundle(bundle,expected_receipt_sha256):
    bundle=Path(bundle)
    if not bundle.is_dir() or {p.name for p in bundle.iterdir()}!=FILES or any((bundle/name).is_symlink() or not (bundle/name).is_file() for name in FILES):
        raise ValueError('Incomplete migration bundle')
    if type(expected_receipt_sha256) is not str or re.fullmatch('[0-9a-f]{64}',expected_receipt_sha256) is None:
        raise ValueError('External migration receipt digest required')
    data=(bundle/'migration.json').read_bytes()
    if sha(data)!=expected_receipt_sha256:raise ValueError('Migration receipt digest mismatch')
    receipt=json.loads(data.decode('utf8'),object_pairs_hook=unique_object)
    if type(receipt) is not dict or set(receipt)!={'revision','legacy_revision','current_revision','legacy_sha256','current_sha256','certificate_sha256','files'} or receipt['revision']!='TGI-SPATIAL-CYCLE-MIGRATION-BUNDLE-V1' or receipt['legacy_revision']!=LEGACY or receipt['current_revision']!=REVISION or receipt['files']!=['legacy.json','current.json']:
        raise ValueError('Invalid migration receipt')
    old=(bundle/'legacy.json').read_bytes();new=(bundle/'current.json').read_bytes()
    if sha(old)!=receipt['legacy_sha256'] or sha(new)!=receipt['current_sha256']:raise ValueError('Migration file digest mismatch')
    envelope=json.loads(old.decode('utf8'),object_pairs_hook=unique_object)
    if type(envelope) is not dict or set(envelope)!={'payload','sha256'} or type(envelope['payload']) is not dict:
        raise ValueError('Invalid legacy checkpoint in bundle')
    payload=envelope['payload']
    if set(payload)!={'revision','registry','raw_episodes','actions','certificate'} or payload['revision']!=LEGACY or payload['registry']!=REGISTRY_ID or sha(canonical(payload).encode())!=envelope['sha256']:
        raise ValueError('Invalid legacy checkpoint in bundle')
    cycle=SpatialRelationCycle.recover(bundle/'current.json',receipt['current_sha256'])
    if canonical(cycle.certificate)!=canonical(envelope['payload']['certificate']) or sha(canonical(cycle.certificate).encode())!=receipt['certificate_sha256']:
        raise ValueError('Migration certificate mismatch')
    return cycle,receipt






"""Research-only incremental lifecycle for phase-owned raw action relations."""
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from .frame_engine import canonical, unique_object
from .identity import decode, REGISTRY_ID
from .organization import RawOrganization

from .spatial_direct_action_relation import form_direct_raw_relations
from .spatial_direct_action_relation_check import verify_direct_raw_relation

REVISION = 'TGI-M1-DIRECT-RAW-ACTION-CYCLE-V1'


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _fork_phase_model(parent):
    if type(parent) is not RawOrganization or parent.frames._pending:
        raise ValueError('Complete raw phase model required')
    child = RawOrganization()
    for name in ('_atoms', '_bonds', '_origins', '_contexts', '_sources', '_pending'):
        setattr(child.frames, name, dict(getattr(parent.frames, name)))
    child.episodes = dict(parent.episodes)
    child._dirty = bool(child.episodes)
    return child


class DirectRawActionCycle:
    def __init__(self, model, commands):
        certificate = form_direct_raw_relations(model, commands)
        if not verify_direct_raw_relation(model, commands, certificate):
            raise ValueError('Independent phase relation verification failed')
        self.model = model
        self.commands = json.loads(json.dumps(commands))
        self.certificate = certificate

    def observe(self, source, frames, action):
        if not verify_direct_raw_relation(self.model, self.commands, self.certificate):
            raise ValueError('Parent phase relation changed before append')
        child = _fork_phase_model(self.model)
        child.observe(source, frames)
        return type(self)(child, self.commands + [{'source': source, 'action': action}])

    def commit(self, path):
        if not verify_direct_raw_relation(self.model, self.commands, self.certificate):
            raise ValueError('Phase relation changed before commit')
        payload = {'revision': REVISION, 'registry': REGISTRY_ID,
                   'raw_episodes': [{'source': source, 'frames': [decode(frame) for frame in frames]}
                                    for source, (frames, _) in self.model.episodes.items()],
                   'commands': self.commands, 'certificate': self.certificate}
        envelope = {'payload': payload, 'sha256': _digest(canonical(payload).encode('utf8'))}
        data = canonical(envelope).encode('utf8')
        destination = Path(path)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='wb', dir=destination.parent, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
            temporary = None
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
        return {'path': str(destination), 'sha256': _digest(data), 'bytes': len(data)}

    @classmethod
    def recover(cls, path, expected_sha256):
        if type(expected_sha256) is not str or re.fullmatch(r'[0-9a-f]{64}', expected_sha256) is None:
            raise ValueError('External checkpoint digest required')
        data = Path(path).read_bytes()
        if _digest(data) != expected_sha256:
            raise ValueError('Checkpoint digest mismatch')
        envelope = json.loads(data.decode('utf8'), object_pairs_hook=unique_object)
        if type(envelope) is not dict or set(envelope) != {'payload', 'sha256'}:
            raise ValueError('Invalid checkpoint envelope')
        payload = envelope['payload']
        if (type(payload) is not dict or set(payload) != {'revision', 'registry', 'raw_episodes', 'commands', 'certificate'} or
                payload['revision'] != REVISION or payload['registry'] != REGISTRY_ID or
                _digest(canonical(payload).encode('utf8')) != envelope['sha256'] or
                type(payload['raw_episodes']) is not list):
            raise ValueError('Invalid checkpoint payload')
        model = RawOrganization()
        for row in payload['raw_episodes']:
            if type(row) is not dict or set(row) != {'source', 'frames'}:
                raise ValueError('Original raw episode required')
            model.observe(row['source'], row['frames'])
        cycle = cls(model, payload['commands'])
        if canonical(cycle.certificate) != canonical(payload['certificate']):
            raise ValueError('Reconstructed relation mismatch')
        return cycle

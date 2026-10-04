"""Owned V10 research cycle with local epoch updates and cold proof recovery."""
import copy
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from .frame_engine import canonical, unique_object
from .identity import REGISTRY_ID, decode
from .organization import RawOrganization
from .spatial_contextual_action_cycle import OwnedContextualRawActionCycle
from .spatial_local_action_relation import event_from_new_raw_pair
from .spatial_temporal_action_phase import form_temporal_phase, resolve_temporal_phase
from .spatial_temporal_action_phase_check import verify_temporal_phase
from .spatial_temporal_action_local import append_temporal_phase

REVISION = 'TGI-S2-TEMPORAL-EPOCH-CYCLE-V10'


def _digest(data):
    return hashlib.sha256(data).hexdigest()


class OwnedTemporalRawActionCycle(OwnedContextualRawActionCycle):
    __slots__ = ('_temporal',)

    def __init__(self, model, commands):
        super().__init__(model, commands)
        temporal = form_temporal_phase(self.model, self.commands)
        if not verify_temporal_phase(self.model, self.commands, temporal):
            raise ValueError('Initial temporal phase not independently verified')
        self._temporal = temporal

    @property
    def certificate(self):
        return copy.deepcopy(self._temporal)

    def observe(self, source, frames, action):
        child = OwnedContextualRawActionCycle.observe(self, source, frames, action)
        event = event_from_new_raw_pair(child._local._model, source, action)
        child._temporal = append_temporal_phase(self._temporal, child._contextual,
                                                event, child._local._commands)
        return child

    def resolve(self, anchor, before_nmu):
        return resolve_temporal_phase(self._temporal, anchor, before_nmu)

    def verify_full(self):
        return (OwnedContextualRawActionCycle.verify_full(self) and
                self._temporal['spatial_certificate'] == self._contextual and
                self._temporal == form_temporal_phase(self.model, self.commands) and
                verify_temporal_phase(self.model, self.commands, self._temporal))

    def commit(self, path):
        if not self.verify_full():
            raise ValueError('Full temporal replay failed before checkpoint')
        model = self.model
        payload = {'revision': REVISION, 'registry': REGISTRY_ID,
                   'raw_episodes': [{'source': source,
                                     'frames': [decode(frame) for frame in frames]}
                                    for source, (frames, _) in model.episodes.items()],
                   'commands': self.commands,
                   'direct_certificate': self.direct_certificate,
                   'contextual_certificate': self._contextual,
                   'temporal_certificate': self._temporal}
        envelope = {'payload': payload,
                    'sha256': _digest(canonical(payload).encode('utf8'))}
        data = canonical(envelope).encode('utf8')
        destination = Path(path)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='wb', dir=destination.parent,
                                             delete=False) as stream:
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
        if (type(payload) is not dict or
                set(payload) != {'revision', 'registry', 'raw_episodes', 'commands',
                                 'direct_certificate', 'contextual_certificate',
                                 'temporal_certificate'} or
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
        if (canonical(cycle.direct_certificate) != canonical(payload['direct_certificate']) or
                canonical(cycle._contextual) != canonical(payload['contextual_certificate']) or
                canonical(cycle.certificate) != canonical(payload['temporal_certificate'])):
            raise ValueError('Reconstructed temporal phase mismatch')
        return cycle

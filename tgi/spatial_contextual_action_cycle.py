"""Owned raw action lifecycle with conflict-preserving contextual phase."""
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
from .spatial_direct_action_cycle import _fork_phase_model
from .spatial_local_action_cycle import OwnedLocalRawActionCycle
from .spatial_local_action_relation import event_from_new_raw_pair
from .spatial_contextual_action_phase import form_contextual_phase, resolve_contextual_phase
from .spatial_contextual_action_phase_check import verify_contextual_phase
from .spatial_contextual_action_local import append_contextual_family

REVISION = 'TGI-S2-CONTEXTUAL-ACTION-CYCLE-V1'


def _digest(data):
    return hashlib.sha256(data).hexdigest()


class OwnedContextualRawActionCycle:
    __slots__ = ('_local', '_contextual')

    def __init__(self, model, commands):
        local = OwnedLocalRawActionCycle(model, commands)
        contextual = form_contextual_phase(local.model, local.commands)
        if not verify_contextual_phase(local.model, local.commands, contextual):
            raise ValueError('Initial contextual phase not independently verified')
        self._local = local
        self._contextual = contextual

    @property
    def model(self):
        return self._local.model

    @property
    def commands(self):
        return self._local.commands

    @property
    def direct_certificate(self):
        return self._local.certificate

    @property
    def certificate(self):
        return copy.deepcopy(self._contextual)

    def observe(self, source, frames, action):
        local = self._local.observe(source, frames, action)
        event = event_from_new_raw_pair(local._model, source, action)
        contextual = append_contextual_family(self._contextual,
                                               local._certificate, event)
        child = object.__new__(type(self))
        child._local = local
        child._contextual = contextual
        return child

    def resolve(self, anchor, before_nmu):
        return resolve_contextual_phase(self._contextual, anchor, before_nmu)

    def verify_full(self):
        return (self._local.verify_full() and
                self._contextual['direct_certificate'] == self._local.certificate and
                verify_contextual_phase(self._local.model, self._local.commands,
                                        self._contextual))

    def commit(self, path):
        if not self.verify_full():
            raise ValueError('Full contextual replay failed before checkpoint')
        model = self._local.model
        payload = {'revision': REVISION, 'registry': REGISTRY_ID,
                   'raw_episodes': [{'source': source,
                                     'frames': [decode(frame) for frame in frames]}
                                    for source, (frames, _) in model.episodes.items()],
                   'commands': self._local.commands,
                   'direct_certificate': self._local.certificate,
                   'contextual_certificate': self._contextual}
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
                                 'direct_certificate', 'contextual_certificate'} or
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
                canonical(cycle.certificate) != canonical(payload['contextual_certificate'])):
            raise ValueError('Reconstructed contextual phase mismatch')
        return cycle

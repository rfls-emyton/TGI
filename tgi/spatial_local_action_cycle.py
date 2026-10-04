"""Research-only owned lifecycle for local raw relation transitions."""
import copy

from .spatial_direct_action_cycle import _fork_phase_model
from .spatial_direct_action_cycle import DirectRawActionCycle
from .spatial_direct_action_relation import form_direct_raw_relations
from .spatial_direct_action_relation_check import verify_direct_raw_relation
from .spatial_local_action_relation import append_verified_event, event_from_new_raw_pair


class OwnedLocalRawActionCycle:
    __slots__ = ('_model', '_commands', '_certificate')

    def __init__(self, model, commands):
        owned = _fork_phase_model(model)
        saved_commands = copy.deepcopy(commands)
        certificate = form_direct_raw_relations(owned, saved_commands)
        if not verify_direct_raw_relation(owned, saved_commands, certificate):
            raise ValueError('Initial relation not independently verified')
        self._model = owned
        self._commands = saved_commands
        self._certificate = certificate

    @property
    def model(self):
        return _fork_phase_model(self._model)

    @property
    def commands(self):
        return copy.deepcopy(self._commands)

    @property
    def certificate(self):
        return copy.deepcopy(self._certificate)

    def observe(self, source, frames, action):
        child_model = _fork_phase_model(self._model)
        child_model.observe(source, frames)
        event = event_from_new_raw_pair(child_model, source, action)
        child_certificate = append_verified_event(self._certificate, event)
        child = object.__new__(type(self))
        child._model = child_model
        child._commands = self._commands + [{'source': source, 'action': action}]
        child._certificate = child_certificate
        return child

    def verify_full(self):
        return verify_direct_raw_relation(self._model, self._commands, self._certificate)

    def commit(self, path):
        if not self.verify_full():
            raise ValueError('Full relation replay failed before checkpoint')
        replay = DirectRawActionCycle(self.model, self.commands)
        if replay.certificate != self._certificate:
            raise ValueError('Incremental and full certificates diverged')
        return replay.commit(path)

    @classmethod
    def recover(cls, path, expected_sha256):
        replay = DirectRawActionCycle.recover(path, expected_sha256)
        return cls(replay.model, replay.commands)


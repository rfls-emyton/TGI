"""Source-owned spatial action observation without an externally supplied port."""
from pathlib import Path

from .frame_engine import canonical
from .identity import decode
from .organization_inventory_check import verify_organization_inventory
from .organization_snapshot import snapshot
from .spatial_action_relation_cycle import SpatialRelationCycle


def _port(before, after):
    if type(before) is not str or type(after) is not str or len(before) != len(after):
        raise ValueError('Equal-length raw frame pair required')
    changed = [index for index, (left, right) in enumerate(zip(before, after)) if left != right]
    if (len(changed) != 1 or before[changed[0]] == '.' or
            after[changed[0]] == '.'):
        raise ValueError('Unique persistent occurrence change required')
    return changed[0]


def derive_observed_actions(model, commands, *, max_search_steps=100000):
    """Locate each action's affected occurrence from its phase-valid raw pair."""
    if type(commands) is not list or model._dirty or not verify_organization_inventory(model, max_search_steps=max_search_steps):
        raise ValueError('Complete phase-valid organization inventory required')
    view = snapshot(model)
    actions, seen = [], set()
    for command in commands:
        if type(command) is not dict or set(command) != {'source', 'action'}:
            raise ValueError('Source-owned raw command without port required')
        source, action = command['source'], command['action']
        if (type(source) is not str or type(action) is not str or not action or
                source in seen or source not in view.episodes or not view._alive(source)):
            raise ValueError('Unique alive source and raw action required')
        seen.add(source)
        frames, _ = view.episodes[source]
        if len(frames) != 2:
            raise ValueError('Before/after raw pair required')
        before, after = map(decode, frames)
        actions.append({'source': source, 'action': action, 'port': _port(before, after)})
    return actions


class ObservedSpatialRelationCycle:
    """Continual relation cycle whose public observations contain no port label."""

    def __init__(self, model, commands, *, max_search_steps=100000):
        actions = derive_observed_actions(model, commands, max_search_steps=max_search_steps)
        self._cycle = SpatialRelationCycle(model, actions, max_search_steps=max_search_steps)
        self.commands = [{'source': item['source'], 'action': item['action']} for item in commands]
        self.max_search_steps = max_search_steps

    @property
    def certificate(self):
        return self._cycle.certificate

    @property
    def model(self):
        return self._cycle.model

    def observe(self, source, frames, action):
        if type(frames) is not list or len(frames) != 2:
            raise ValueError('Before/after raw pair required')
        port = _port(frames[0], frames[1])
        successor = self._cycle.observe(source, frames, action, port)
        result = object.__new__(type(self))
        result._cycle = successor
        result.commands = self.commands + [{'source': source, 'action': action}]
        result.max_search_steps = self.max_search_steps
        if canonical(derive_observed_actions(result.model, result.commands, max_search_steps=self.max_search_steps)) != canonical(successor.actions):
            raise ValueError('Inferred port does not match retained raw experience')
        return result

    def commit(self, path):
        if canonical(derive_observed_actions(self.model, self.commands, max_search_steps=self.max_search_steps)) != canonical(self._cycle.actions):
            raise ValueError('Inferred port changed before commit')
        return self._cycle.commit(path)

    @classmethod
    def recover(cls, path, expected_sha256, *, max_search_steps=100000):
        cycle = SpatialRelationCycle.recover(path, expected_sha256, max_search_steps=max_search_steps)
        commands = [{'source': item['source'], 'action': item['action']} for item in cycle.actions]
        if canonical(derive_observed_actions(cycle.model, commands, max_search_steps=max_search_steps)) != canonical(cycle.actions):
            raise ValueError('Checkpoint port is not derived from raw experience')
        result = object.__new__(cls)
        result._cycle = cycle
        result.commands = commands
        result.max_search_steps = max_search_steps
        return result

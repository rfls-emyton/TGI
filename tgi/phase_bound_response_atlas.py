"""Independent local response crystals over original phase-bound NMU streams."""

import copy
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from .frame_engine import canonical, unique_object
from .identity import REGISTRY_ID, encode
from .organization import OMEGA_CRIT
from .phase_bound_port_classes import PhaseBoundResponseIncidenceClasses

REVISION = 'TGI-M2-PHASE-BOUND-RESPONSE-ATLAS-V1'


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _atlas_reference(events):
    """Reform action-conditioned local C/L cells after each raw experience."""
    births, previous_groups, previous_roles = {}, set(), set()
    phases = []
    for index, event in enumerate(events):
        names = sorted(event['ports'])
        actions = sorted({tuple(encode(row['action'])) for row in events[:index+1]})
        cells, roles, groups = [], set(), set()
        for action_nmu in actions:
            action_events = [row for row in events[:index+1]
                             if tuple(encode(row['action'])) == action_nmu]
            grouped = {}
            for name in names:
                trace = tuple(row['ports'][name][0] != row['ports'][name][1]
                              for row in action_events)
                grouped.setdefault(trace, []).append(name)
            for members in sorted(tuple(value) for value in grouped.values()):
                key = (action_nmu, members)
                groups.add(key)
                born_at = births[key] if key in previous_groups else index
                changed_contexts, changed_all, stable_contexts, comparator_actions = set(), set(), set(), set()
                controls = 0
                for position, row in enumerate(events[:index+1]):
                    action = tuple(encode(row['action']))
                    before = tuple(tuple(encode(row['ports'][name][0])) for name in members)
                    changed = all(row['ports'][name][0] != row['ports'][name][1]
                                  for name in members)
                    stable = all(row['ports'][name][0] == row['ports'][name][1]
                                 for name in members)
                    if action == action_nmu:
                        if changed:
                            changed_all.add(before)
                            if position >= born_at:
                                changed_contexts.add(before)
                        if stable:
                            stable_contexts.add(before)
                            controls += 1
                    elif stable and any(row['ports'][name][0] != row['ports'][name][1]
                                        for name in names if name not in members):
                        comparator_actions.add(action)
                opposition = bool(changed_all & stable_contexts)
                eligible = (len(changed_contexts) >= OMEGA_CRIT and controls > 0
                            and bool(comparator_actions) and not opposition)
                cell = {'action_nmu': list(action_nmu), 'members': list(members),
                        'born_at': born_at, 'omega': len(changed_contexts),
                        'controls': controls, 'comparator': bool(comparator_actions),
                        'opposition': opposition, 'xi': int(eligible)}
                cells.append(cell)
                if eligible:
                    roles.add(key)
        revoked = previous_roles - roles
        admitted = [{'action_nmu': list(action), 'members': list(members)}
                    for action, members in sorted(roles)]
        removed = [{'action_nmu': list(action), 'members': list(members)}
                   for action, members in sorted(revoked)]
        phases.append({'event_index': index, 'source': event['source'],
                       'classes': cells, 'admitted': admitted, 'revoked': removed,
                       'status': 'CRYSTAL' if admitted else 'REVOKED' if removed else 'NO_PATH'})
        births = {key: births[key] if key in previous_groups else index
                  for key in groups}
        previous_groups, previous_roles = groups, roles
    return {'revision': REVISION, 'registry': REGISTRY_ID, 'phases': phases,
            'decision': phases[-1] if phases else
            {'event_index': None, 'source': None, 'classes': [], 'admitted': [],
             'revoked': [], 'status': 'NO_PATH'}}


def _atlas(events):
    """Accumulate original per-action traces and live-class C/L state."""
    births, previous_groups, previous_roles, previous_stats = {}, set(), set(), {}
    traces, prepared, phases = {}, [], []
    for index, event in enumerate(events):
        names = sorted(event['ports'])
        action = tuple(encode(event['action']))
        changed = {name: event['ports'][name][0] != event['ports'][name][1]
                   for name in names}
        before = {name: tuple(encode(event['ports'][name][0])) for name in names}
        prepared.append((action, changed, before))
        if action not in traces:
            traces[action] = {name: () for name in names}
        for name in names:
            traces[action][name] += (changed[name],)
        cells, roles, groups, current_stats = [], set(), set(), {}
        for wanted in sorted(traces):
            grouped = {}
            for name in names:
                grouped.setdefault(traces[wanted][name], []).append(name)
            for members in sorted(tuple(value) for value in grouped.values()):
                key = (wanted, members)
                groups.add(key)
                born = births[key] if key in previous_groups else index
                if key in previous_groups:
                    stats = previous_stats[key]
                    history = ((index, prepared[-1]),)
                else:
                    stats = {'changed_all': set(), 'changed_contexts': set(),
                             'stable_contexts': set(), 'controls': 0,
                             'comparator_actions': set()}
                    history = enumerate(prepared)
                for position, (row_action, row_changed, row_before) in history:
                    stable = all(not row_changed[name] for name in members)
                    changed_all = all(row_changed[name] for name in members)
                    if row_action == wanted:
                        context = tuple(row_before[name] for name in members)
                        if changed_all:
                            stats['changed_all'].add(context)
                            if position >= born:
                                stats['changed_contexts'].add(context)
                        if stable:
                            stats['stable_contexts'].add(context)
                            stats['controls'] += 1
                    elif stable and any(row_changed[name] for name in names
                                        if name not in members):
                        stats['comparator_actions'].add(row_action)
                current_stats[key] = stats
                opposed = bool(stats['changed_all'] & stats['stable_contexts'])
                eligible = (len(stats['changed_contexts']) >= OMEGA_CRIT and
                            stats['controls'] > 0 and
                            bool(stats['comparator_actions']) and not opposed)
                cells.append({'action_nmu': list(wanted), 'members': list(members),
                              'born_at': born,
                              'omega': len(stats['changed_contexts']),
                              'controls': stats['controls'],
                              'comparator': bool(stats['comparator_actions']),
                              'opposition': opposed, 'xi': int(eligible)})
                if eligible:
                    roles.add(key)
        admitted = [{'action_nmu': list(action), 'members': list(members)}
                    for action, members in sorted(roles)]
        revoked = [{'action_nmu': list(action), 'members': list(members)}
                   for action, members in sorted(previous_roles - roles)]
        phases.append({'event_index': index, 'source': event['source'],
                       'classes': cells, 'admitted': admitted, 'revoked': revoked,
                       'status': 'CRYSTAL' if admitted else 'REVOKED' if revoked
                       else 'NO_PATH'})
        births = {key: births[key] if key in previous_groups else index
                  for key in groups}
        previous_groups, previous_roles, previous_stats = groups, roles, current_stats
    return {'revision': REVISION, 'registry': REGISTRY_ID, 'phases': phases,
            'decision': phases[-1] if phases else
            {'event_index': None, 'source': None, 'classes': [], 'admitted': [],
             'revoked': [], 'status': 'NO_PATH'}}


class PhaseBoundResponseAtlas:
    """Multiple local classes with live C/L, Ω, ξ, bond and NMU source checks."""

    def __init__(self, events=(), *, max_search_steps=100000):
        self._bound = PhaseBoundResponseIncidenceClasses(
            events, max_search_steps=max_search_steps)
        self._events = copy.deepcopy(self._bound._events)
        self._events_digest = _sha(canonical(self._events).encode('utf8'))
        self._formed = _atlas(self._events)
        self._formed_digest = _sha(canonical(self._formed).encode('utf8'))
        from .phase_bound_response_atlas_check import verify
        if not verify(self._events, self._formed):
            raise ValueError('Independent local atlas replay failed')
        self.max_search_steps = max_search_steps

    @property
    def certificate(self):
        bound = self._bound.certificate
        if _sha(canonical(self._events).encode('utf8')) != self._events_digest:
            raise ValueError('Original atlas event changed')
        if _sha(canonical(self._formed).encode('utf8')) != self._formed_digest:
            raise ValueError('Local response atlas changed')
        return {'revision': REVISION, 'registry': REGISTRY_ID,
                'bound_source_sha256': _sha(canonical(bound).encode('utf8')),
                'atlas': copy.deepcopy(self._formed)}

    def resolve(self, action):
        return self.resolve_batch([action])[0]

    def resolve_batch(self, actions):
        """One live source verification for an ordered batch of raw actions."""
        return self.resolve_batch_with_certificate(actions)[1]

    def resolve_batch_with_certificate(self, actions):
        """Return one verified source snapshot and its ordered action roles."""
        if type(actions) not in (list, tuple) or not actions or \
                any(type(action) is not str or not action for action in actions):
            raise ValueError('Nonempty ordered raw actions required')
        wanted = [list(encode(action)) for action in actions]
        certificate = self.certificate
        decision = certificate['atlas']['decision']['admitted']
        result = [[row['members'] for row in decision if row['action_nmu'] == action]
                  for action in wanted]
        return certificate, [members or None for members in result]

    def observe(self, source, action, ports):
        self.certificate
        return type(self)(self._events + [{'source': source, 'action': action,
                                            'ports': copy.deepcopy(ports)}],
                          max_search_steps=self.max_search_steps)

    def observe_batch(self, events):
        self.certificate
        if type(events) not in (list, tuple) or not events:
            raise ValueError('Nonempty ordered event batch required')
        return type(self)(self._events + copy.deepcopy(list(events)),
                          max_search_steps=self.max_search_steps)

    def commit(self, path):
        certificate = self.certificate
        payload = {'revision': REVISION, 'registry': REGISTRY_ID,
                   'events': self._events, 'certificate': certificate}
        envelope = {'payload': payload, 'sha256': _sha(canonical(payload).encode('utf8'))}
        data = canonical(envelope).encode('utf8')
        target = Path(path)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='wb', dir=target.parent,
                                             delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
            temporary = None
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
        return {'path': str(target), 'sha256': _sha(data), 'bytes': len(data)}

    @classmethod
    def recover(cls, path, expected_sha256, *, max_search_steps=100000):
        if type(expected_sha256) is not str or re.fullmatch('[0-9a-f]{64}', expected_sha256) is None:
            raise ValueError('External checkpoint digest required')
        data = Path(path).read_bytes()
        if _sha(data) != expected_sha256:
            raise ValueError('Checkpoint digest mismatch')
        envelope = json.loads(data.decode('utf8'), object_pairs_hook=unique_object)
        if type(envelope) is not dict or set(envelope) != {'payload', 'sha256'} or \
                envelope['sha256'] != _sha(canonical(envelope['payload']).encode('utf8')):
            raise ValueError('Invalid atlas checkpoint envelope')
        payload = envelope['payload']
        if type(payload) is not dict or set(payload) != {'revision', 'registry', 'events', 'certificate'} or \
                payload['revision'] != REVISION or payload['registry'] != REGISTRY_ID:
            raise ValueError('Invalid atlas checkpoint payload')
        result = cls(payload['events'], max_search_steps=max_search_steps)
        if canonical(result.certificate) != canonical(payload['certificate']):
            raise ValueError('Recomputed atlas certificate differs')
        return result

"""Owned append with independent one-pass complete replay."""
import copy
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from tgi.frame_engine import canonical, unique_object
from tgi.identity import REGISTRY_ID, encode
from tgi.organization import OMEGA_CRIT
from tgi.intervention_edit_contrast import contrast

REVISION = 'TGI-M1-CROSS-ACTION-PROFILE-RESEARCH-V3'


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _contrast(before, after):
    return contrast(before, after)


def _event(source, action, target_before, target_after, views):
    if type(source) is not str or not source or type(action) is not str or not action:
        raise ValueError('Original source and action required')
    if type(views) is not dict or len(views) < 2:
        raise ValueError('At least two original view streams required')
    target = _contrast(target_before, target_after)
    measured = {}
    for name, frames in sorted(views.items()):
        if type(name) is not str or not name or type(frames) not in (tuple, list) or len(frames) != 2:
            raise ValueError('Original view address and before/after frames required')
        measured[name] = _contrast(*frames)
    return {'source': source, 'action_nmu': list(encode(action)),
            'target': target, 'views': measured}


def form(events):
    """Accumulate original events once while retaining every V3 phase field."""
    if type(events) is not list:
        raise ValueError('Original chronological event list required')
    if not events:
        return {'revision': REVISION, 'registry': REGISTRY_ID, 'events': [],
                'phases': [], 'result': {'status': 'NO_PATH', 'view': None}}
    names = list(events[0]['views'])
    if len(names) < 2:
        raise ValueError('At least two view streams required')
    sources = set()
    prior_crystal = None
    phases = []
    actions = set()
    comparator = set()
    support = {name: {} for name in names}
    controls = {name: {} for name in names}
    opposing = {name: [] for name in names}
    for index, event in enumerate(events):
        if (type(event) is not dict or set(event) != {'source', 'action_nmu',
                'target', 'views'} or event['source'] in sources or
                list(event['views']) != names):
            raise ValueError('Unique raw event and fixed view inventory required')
        sources.add(event['source'])
        action = tuple(event['action_nmu'])
        actions.add(action)
        if not event['target']['changed'] and any(
                view['changed'] for view in event['views'].values()):
            comparator.add(action)
        cells = []
        eligible = []
        for name in names:
            owned_support = support[name]
            owned_controls = controls[name]
            owned_support.setdefault(action, set())
            owned_controls.setdefault(action, 0)
            if event['target']['changed'] and event['views'][name]['changed']:
                owned_support[action].add(tuple(event['target']['before_nmu']))
            elif not event['target']['changed'] and not event['views'][name]['changed']:
                owned_controls[action] += 1
            else:
                opposing[name].append(event['source'])
            positives = [candidate for candidate in sorted(actions)
                         if len(owned_support.get(candidate, ())) >= OMEGA_CRIT and
                         owned_controls.get(candidate, 0) > 0]
            if not opposing[name] and any(other != candidate for candidate in positives
                                    for other in comparator):
                eligible.append(name)
            cells.append({'view': name,
                          'omega_by_action': [{'action_nmu': list(candidate),
                                               'omega': len(owned_support.get(candidate, ())),
                                               'controls': owned_controls.get(candidate, 0)}
                                              for candidate in sorted(actions)],
                          'contradicting_sources': list(opposing[name]),
                          'xi': 0})
        result = ({'status': 'CRYSTAL', 'view': eligible[0]}
                  if len(eligible) == 1 else
                  {'status': 'REVOKED', 'view': None}
                  if prior_crystal is not None and prior_crystal not in eligible else
                  {'status': 'NO_PATH', 'view': None})
        if result['status'] == 'CRYSTAL':
            prior_crystal = result['view']
            for cell in cells:
                cell['xi'] = int(cell['view'] == result['view'])
        phases.append({'event_index': index, 'source': event['source'],
                       'comparator_actions': [list(candidate) for candidate in sorted(comparator)],
                       'cells': cells, 'result': result})
    return {'revision': REVISION, 'registry': REGISTRY_ID,
            'events': list(events), 'phases': phases,
            'result': copy.deepcopy(phases[-1]['result'])}


class OwnedInterventionCorrespondence:
    def __init__(self, events=None):
        from tgi.cross_action_correspondence_check import verify
        self._events = copy.deepcopy([] if events is None else events)
        self._certificate = form(self._events)
        if not verify(self._events, self._certificate):
            raise ValueError('Invalid original raw correspondence history')

    @property
    def certificate(self):
        return copy.deepcopy(self._certificate)

    def observe(self, source, action, target_before, target_after, views):
        event = _event(source, action, target_before, target_after, views)
        if any(row['source'] == source for row in self._events):
            raise ValueError('Duplicate original source')
        from tgi.cross_action_correspondence_check import verify
        child = type(self).__new__(type(self))
        child._events = self._events + [event]
        child._certificate = form(child._events)
        if not verify(child._events, child._certificate):
            raise ValueError('Invalid original raw correspondence history')
        return child

    def resolve(self):
        return copy.deepcopy(self._certificate['result'])

    def commit(self, path):
        from tgi.cross_action_correspondence_check import verify
        if not verify(self._events, self._certificate):
            raise ValueError('Independent raw correspondence replay failed')
        payload = {'revision': REVISION, 'registry': REGISTRY_ID,
                   'events': self._events, 'certificate': self._certificate}
        envelope = {'payload': payload, 'sha256': _sha(canonical(payload).encode('utf8'))}
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
        return {'path': str(destination), 'sha256': _sha(data), 'bytes': len(data)}

    @classmethod
    def recover(cls, path, expected_sha256):
        from tgi.cross_action_correspondence_check import verify
        if type(expected_sha256) is not str or re.fullmatch(r'[0-9a-f]{64}', expected_sha256) is None:
            raise ValueError('External checkpoint digest required')
        data = Path(path).read_bytes()
        if _sha(data) != expected_sha256:
            raise ValueError('Checkpoint digest mismatch')
        envelope = json.loads(data.decode('utf8'), object_pairs_hook=unique_object)
        if type(envelope) is not dict or set(envelope) != {'payload', 'sha256'}:
            raise ValueError('Invalid checkpoint envelope')
        payload = envelope['payload']
        if (type(payload) is not dict or set(payload) != {'revision', 'registry',
                'events', 'certificate'} or payload['revision'] != REVISION or
                payload['registry'] != REGISTRY_ID or
                _sha(canonical(payload).encode('utf8')) != envelope['sha256'] or
                not verify(payload['events'], payload['certificate'])):
            raise ValueError('Invalid raw correspondence checkpoint')
        return cls(payload['events'])

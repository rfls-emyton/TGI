"""V2 raw intervention correspondence over one-occurrence NMU edits."""
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

REVISION = 'TGI-M1-INTERVENTION-CORRESPONDENCE-RESEARCH-V2'


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
    """Rebuild every phase from retained original ordered raw contrast events."""
    if type(events) is not list:
        raise ValueError('Original chronological event list required')
    if not events:
        return {'revision': REVISION, 'registry': REGISTRY_ID, 'events': [],
                'phases': [], 'result': {'status': 'NO_PATH', 'view': None}}
    names = list(events[0]['views'])
    action = events[0]['action_nmu']
    if len(names) < 2:
        raise ValueError('At least two view streams required')
    sources = set()
    support = {name: set() for name in names}
    contradicted = {name: [] for name in names}
    controls = 0
    prior_crystal = None
    phases = []
    for index, event in enumerate(events):
        if (type(event) is not dict or set(event) != {'source', 'action_nmu',
                'target', 'views'} or event['source'] in sources or
                list(event['views']) != names or event['action_nmu'] != action):
            raise ValueError('Unique raw event, fixed view inventory and same measured action required')
        sources.add(event['source'])
        if not event['target']['changed']:
            controls += 1
        for name in names:
            if event['views'][name]['changed'] == event['target']['changed']:
                if event['target']['changed']:
                    support[name].add(tuple(event['target']['before_nmu']))
            else:
                contradicted[name].append(event['source'])
        eligible = [name for name in names if not contradicted[name] and
                    len(support[name]) >= OMEGA_CRIT and controls > 0]
        result = ({'status': 'CRYSTAL', 'view': eligible[0]}
                  if len(eligible) == 1 else
                  {'status': 'REVOKED', 'view': None}
                  if prior_crystal is not None and prior_crystal not in eligible else
                  {'status': 'NO_PATH', 'view': None})
        if result['status'] == 'CRYSTAL':
            prior_crystal = result['view']
        cells = [{'view': name, 'omega': len(support[name]),
                  'xi': int(result['status'] == 'CRYSTAL' and result['view'] == name),
                  'contradicting_sources': list(contradicted[name])}
                 for name in names]
        phases.append({'event_index': index, 'source': event['source'],
                       'controls': controls, 'cells': cells, 'result': result})
    return {'revision': REVISION, 'registry': REGISTRY_ID,
            'events': copy.deepcopy(events), 'phases': phases,
            'result': copy.deepcopy(phases[-1]['result'])}


class OwnedInterventionCorrespondence:
    def __init__(self, events=None):
        from tgi.intervention_correspondence_check import verify
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
        child = type(self)(self._events + [event])
        return child

    def resolve(self):
        return copy.deepcopy(self._certificate['result'])

    def commit(self, path):
        from tgi.intervention_correspondence_check import verify
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
        from tgi.intervention_correspondence_check import verify
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

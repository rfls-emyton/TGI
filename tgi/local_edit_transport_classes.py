"""Unlabeled classes formed from local NMU edit transport across wrappers."""
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

REVISION = 'TGI-M1-LOCAL-EDIT-TRANSPORT-CLASSES-RESEARCH-V4'


def _transport(row):
    kind = row['kind']
    if kind == 'STABLE':
        return ('STABLE',)
    values = row['positions']
    if kind == 'SUBSTITUTE':
        if len(values) != 1:
            raise ValueError('Single NMU substitution required')
        offset = values[0]
        return (kind, row['before_nmu'][offset], row['after_nmu'][offset])
    if kind == 'INSERT':
        changed = {row['after_nmu'][offset] for offset in values}
    elif kind == 'DELETE':
        changed = {row['before_nmu'][offset] for offset in values}
    else:
        raise ValueError('Unknown one-NMU edit kind')
    if len(changed) != 1:
        raise ValueError('Ambiguous changed NMU identity')
    return (kind, next(iter(changed)))


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _event(source, action, ports):
    if type(source) is not str or not source or type(action) is not str or not action:
        raise ValueError('Original source and action required')
    if type(ports) is not dict or len(ports) < 3:
        raise ValueError('At least three original port streams required')
    rows = {}
    for name, pair in sorted(ports.items()):
        if (type(name) is not str or not name or type(pair) not in (tuple, list) or
                len(pair) != 2):
            raise ValueError('Raw port address and frame pair required')
        rows[name] = contrast(*pair)
    return {'source': source, 'action_nmu': list(encode(action)), 'ports': rows}


def _apply(stats, members, event, names):
    action = tuple(event['action_nmu'])
    changed = all(event['ports'][name]['changed'] for name in members)
    stable = all(not event['ports'][name]['changed'] for name in members)
    if changed:
        context = tuple(tuple(event['ports'][name]['before_nmu']) for name in members)
        stats['support'].setdefault(action, set()).add(context)
    elif stable:
        stats['controls'][action] = stats['controls'].get(action, 0) + 1
        if any(event['ports'][name]['changed'] for name in names if name not in members):
            stats['comparator'].add(action)


def form(events):
    if type(events) is not list:
        raise ValueError('Original chronological event list required')
    phases = []
    seen = set()
    names = None
    previous_class = None
    epoch_start = 0
    traces = {}
    previous_stats = {}
    actions_seen = set()
    for index, event in enumerate(events):
        if (type(event) is not dict or set(event) != {'source', 'action_nmu', 'ports'} or
                event['source'] in seen or type(event['ports']) is not dict):
            raise ValueError('Unique original event required')
        seen.add(event['source'])
        current = list(event['ports'])
        if names is None:
            names = current
            traces = {name: () for name in names}
        if current != names:
            raise ValueError('Fixed port inventory required')
        for name in names:
            row = event['ports'][name]
            traces[name] += (_transport(row),)
        grouped = {}
        for name in names:
            grouped.setdefault(traces[name], []).append(name)
        classes = sorted(tuple(group) for group in grouped.values())
        actions_seen.add(tuple(event['action_nmu']))
        actions = sorted(actions_seen)
        cells = []
        eligible = []
        current_stats = {}
        for members in classes:
            if members in previous_stats:
                stats = previous_stats[members]
                _apply(stats, members, event, names)
            else:
                stats = {'support': {}, 'controls': {}, 'comparator': set()}
                for row in events[epoch_start:index + 1]:
                    _apply(stats, members, row, names)
            current_stats[members] = stats
            counts = []
            for action in actions:
                omega = len(stats['support'].get(action, ()))
                controls = stats['controls'].get(action, 0)
                comparator = any(other != action for other in stats['comparator'])
                counts.append({'action_nmu': list(action), 'omega': omega,
                               'controls': controls, 'comparator': comparator})
                if omega >= OMEGA_CRIT and controls and comparator:
                    eligible.append((action, members))
            cells.append({'members': list(members), 'C_L_by_action': counts, 'xi': 0})
        fractured = previous_class is not None and previous_class not in classes
        if fractured:
            result = {'status': 'REVOKED', 'action_nmu': None, 'members': None}
            previous_class = None
            epoch_start = index + 1
            current_stats = {}
        elif len(eligible) == 1:
            action, members = eligible[0]
            result = {'status': 'CRYSTAL', 'action_nmu': list(action), 'members': list(members)}
            previous_class = members
            for cell in cells:
                cell['xi'] = int(tuple(cell['members']) == members)
        elif previous_class is not None and not any(members == previous_class for _, members in eligible):
            result = {'status': 'REVOKED', 'action_nmu': None, 'members': None}
        else:
            result = {'status': 'NO_PATH', 'action_nmu': None, 'members': None}
        phases.append({'event_index': index, 'source': event['source'],
                       'epoch_start': epoch_start,
                       'classes': cells, 'result': result})
        previous_stats = current_stats
    result = phases[-1]['result'] if phases else {'status': 'NO_PATH', 'action_nmu': None, 'members': None}
    return {'revision': REVISION, 'registry': REGISTRY_ID,
            'events': list(events), 'phases': phases, 'result': result}


class OwnedPortClasses:
    def __init__(self, events=None):
        from tgi.local_edit_transport_classes_check import verify
        self._events = copy.deepcopy([] if events is None else events)
        self._certificate = form(self._events)
        if not verify(self._events, self._certificate):
            raise ValueError('Independent original port replay failed')

    @property
    def certificate(self):
        return copy.deepcopy(self._certificate)

    def observe(self, source, action, ports):
        from tgi.local_edit_transport_classes_check import verify
        if any(row['source'] == source for row in self._events):
            raise ValueError('Duplicate original source')
        event = _event(source, action, ports)
        child = type(self).__new__(type(self))
        child._events = self._events + [event]
        child._certificate = form(child._events)
        if not verify(child._events, child._certificate):
            raise ValueError('Independent original port replay failed')
        return child

    def resolve(self, action):
        result = self._certificate['result']
        if type(action) is not str or not action:
            raise ValueError('Original action trigger required')
        if result['status'] != 'CRYSTAL' or result['action_nmu'] != list(encode(action)):
            return None
        return list(result['members'])

    def commit(self, path):
        from tgi.local_edit_transport_classes_check import verify
        if not verify(self._events, self._certificate):
            raise ValueError('Independent complete replay failed')
        payload = {'revision': REVISION, 'registry': REGISTRY_ID,
                   'events': self._events, 'certificate': self._certificate}
        envelope = {'payload': payload, 'sha256': _sha(canonical(payload).encode('utf8'))}
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
        return {'path': str(destination), 'sha256': _sha(data), 'bytes': len(data)}

    @classmethod
    def recover(cls, path, expected_sha256):
        from tgi.local_edit_transport_classes_check import verify
        if type(expected_sha256) is not str or re.fullmatch(r'[0-9a-f]{64}', expected_sha256) is None:
            raise ValueError('External checkpoint digest required')
        data = Path(path).read_bytes()
        if _sha(data) != expected_sha256:
            raise ValueError('Checkpoint digest mismatch')
        envelope = json.loads(data.decode('utf8'), object_pairs_hook=unique_object)
        if type(envelope) is not dict or set(envelope) != {'payload', 'sha256'}:
            raise ValueError('Invalid checkpoint envelope')
        payload = envelope['payload']
        if (type(payload) is not dict or set(payload) != {'revision', 'registry', 'events', 'certificate'} or
                payload['revision'] != REVISION or payload['registry'] != REGISTRY_ID or
                _sha(canonical(payload).encode('utf8')) != envelope['sha256'] or
                not verify(payload['events'], payload['certificate'])):
            raise ValueError('Invalid original port checkpoint')
        return cls(payload['events'])

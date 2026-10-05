"""NMU-preserving observational classes under sensor-local alphabet changes."""
import copy
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from .frame_engine import canonical, unique_object
from .identity import REGISTRY_ID, encode
from .intervention_edit_contrast import contrast
from .organization import OMEGA_CRIT

REVISION = 'TGI-M1-CAUSAL-PORT-TOPOLOGY-V1'


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _event(source, action, ports):
    if type(source) is not str or not source or type(action) is not str or not action or \
            type(ports) is not dict or len(ports) < 3:
        raise ValueError('Original source, action and three port streams required')
    observed = {}
    for name, pair in sorted(ports.items()):
        if type(name) is not str or not name or type(pair) not in (tuple, list) or len(pair) != 2:
            raise ValueError('Raw port address and frame pair required')
        observed[name] = contrast(*pair)
    return {'source': source, 'action_nmu': list(encode(action)), 'ports': observed}


def _evidence(events, members, names, action):
    contexts = set()
    controls = 0
    comparators = set()
    for event in events:
        key = tuple(event['action_nmu'])
        changed = all(event['ports'][name]['kind'] != 'STABLE' for name in members)
        stable = all(event['ports'][name]['kind'] == 'STABLE' for name in members)
        if changed and key == action:
            contexts.add(tuple(tuple(event['ports'][name]['before_nmu']) for name in members))
        if stable:
            if key == action:
                controls += 1
            if any(event['ports'][name]['kind'] != 'STABLE' for name in names if name not in members):
                comparators.add(key)
    return len(contexts), controls, any(other != action for other in comparators)


def form(events, *, revision=REVISION, valid_row=None):
    if type(events) is not list:
        raise ValueError('Ordered original events required')
    from .intervention_edit_contrast_check import verify as valid_contrast
    if valid_row is None:
        valid_row = valid_contrast
    traces, phases, names, seen, actions = {}, [], None, set(), set()
    prior, epoch = None, 0
    for index, event in enumerate(events):
        if type(event) is not dict or set(event) != {'source', 'action_nmu', 'ports'} or \
                type(event['source']) is not str or not event['source'] or event['source'] in seen or \
                type(event['action_nmu']) is not list or not event['action_nmu'] or \
                type(event['ports']) is not dict:
            raise ValueError('Unique original event required')
        seen.add(event['source'])
        current = list(event['ports'])
        if len(current) < 3 or current != sorted(current) or \
                any(type(name) is not str or not name or not valid_row(event['ports'][name]) for name in current):
            raise ValueError('Complete original port contrasts required')
        if names is None:
            names = current
            traces = {name: [] for name in names}
        if current != names:
            raise ValueError('Fixed port inventory required')
        actions.add(tuple(event['action_nmu']))
        for name in names:
            traces[name].append(event['ports'][name]['kind'])
        grouped = {}
        for name in names:
            grouped.setdefault(tuple(traces[name]), []).append(name)
        groups = sorted(tuple(members) for members in grouped.values())
        cells, winners = [], []
        for members in groups:
            counts = []
            for action in sorted(actions):
                omega, controls, comparator = _evidence(events[epoch:index+1], members, names, action)
                counts.append({'action_nmu': list(action), 'omega': omega,
                               'controls': controls, 'comparator': comparator})
                if omega >= OMEGA_CRIT and controls and comparator:
                    winners.append((action, members))
            cells.append({'members': list(members), 'C_L_by_action': counts, 'xi': 0})
        if prior is not None and prior not in groups:
            result = {'status': 'REVOKED', 'action_nmu': None, 'members': None}
            prior, epoch = None, index + 1
        elif len(winners) == 1:
            action, members = winners[0]
            result = {'status': 'CRYSTAL', 'action_nmu': list(action), 'members': list(members)}
            prior = members
            for cell in cells:
                cell['xi'] = int(tuple(cell['members']) == members)
        elif prior is not None and not any(members == prior for _, members in winners):
            result = {'status': 'REVOKED', 'action_nmu': None, 'members': None}
        else:
            result = {'status': 'NO_PATH', 'action_nmu': None, 'members': None}
        phases.append({'event_index': index, 'source': event['source'],
                       'epoch_start': epoch, 'classes': cells, 'result': result})
    return {'revision': revision, 'registry': REGISTRY_ID, 'events': copy.deepcopy(events),
            'phases': phases, 'result': phases[-1]['result'] if phases else
            {'status': 'NO_PATH', 'action_nmu': None, 'members': None}}


class CausalPortClasses:
    REVISION = REVISION
    EVENT_FACTORY = staticmethod(_event)
    FORM = staticmethod(form)

    @staticmethod
    def VERIFY(events, certificate):
        from .causal_port_classes_check import verify
        return verify(events, certificate)

    def __init__(self, events=()):
        self._events = copy.deepcopy(list(events))
        self._certificate = self.FORM(self._events)
        if not self.VERIFY(self._events, self._certificate):
            raise ValueError('Independent causal topology replay failed')

    def _verify(self):
        if not self.VERIFY(self._events, self._certificate):
            raise ValueError('Original causal state changed')

    @property
    def certificate(self):
        self._verify()
        return copy.deepcopy(self._certificate)

    def observe(self, source, action, ports):
        self._verify()
        if any(row['source'] == source for row in self._events):
            raise ValueError('Duplicate original source')
        return type(self)(self._events + [self.EVENT_FACTORY(source, action, ports)])

    def resolve(self, action):
        self._verify()
        if type(action) is not str or not action:
            raise ValueError('Raw action required')
        result = self._certificate['result']
        return list(result['members']) if result['status'] == 'CRYSTAL' and \
            result['action_nmu'] == list(encode(action)) else None

    def commit(self, path):
        self._verify()
        payload = {'revision': self.REVISION, 'registry': REGISTRY_ID,
                   'events': self._events, 'certificate': self._certificate}
        envelope = {'payload': payload, 'sha256': _sha(canonical(payload).encode('utf8'))}
        data = canonical(envelope).encode('utf8')
        target = Path(path)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='wb', dir=target.parent, delete=False) as stream:
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
    def recover(cls, path, expected_sha256):
        if type(expected_sha256) is not str or re.fullmatch('[0-9a-f]{64}', expected_sha256) is None:
            raise ValueError('External digest required')
        data = Path(path).read_bytes()
        if _sha(data) != expected_sha256:
            raise ValueError('Checkpoint digest mismatch')
        envelope = json.loads(data.decode('utf8'), object_pairs_hook=unique_object)
        if type(envelope) is not dict or set(envelope) != {'payload', 'sha256'}:
            raise ValueError('Invalid checkpoint envelope')
        payload = envelope['payload']
        if type(payload) is not dict or set(payload) != {'revision', 'registry', 'events', 'certificate'} or \
                payload['revision'] != cls.REVISION or payload['registry'] != REGISTRY_ID or \
                _sha(canonical(payload).encode('utf8')) != envelope['sha256']:
            raise ValueError('Invalid checkpoint payload')
        result = cls(payload['events'])
        if canonical(result.certificate) != canonical(payload['certificate']):
            raise ValueError('Recomputed causal certificate differs')
        return result


REVISION_INCIDENCE = 'TGI-M1-RESPONSE-INCIDENCE-V1'


def _response_event(source, action, ports):
    if type(source) is not str or not source or type(action) is not str or not action or \
            type(ports) is not dict or len(ports) < 3:
        raise ValueError('Original source, action and three port streams required')
    observed = {}
    for name, pair in sorted(ports.items()):
        if type(name) is not str or not name or type(pair) not in (tuple, list) or len(pair) != 2 or \
                type(pair[0]) is not str or not pair[0] or type(pair[1]) is not str or not pair[1]:
            raise ValueError('Nonempty raw port frame pair required')
        before, after = list(encode(pair[0])), list(encode(pair[1]))
        changed = before != after
        observed[name] = {'before_nmu': before, 'after_nmu': after,
                          'kind': 'CHANGED' if changed else 'STABLE', 'changed': changed}
    return {'source': source, 'action_nmu': list(encode(action)), 'ports': observed}


def form_incidence(events):
    from .response_incidence_check import valid_response
    return form(events, revision=REVISION_INCIDENCE, valid_row=valid_response)


class ResponseIncidenceClasses(CausalPortClasses):
    REVISION = REVISION_INCIDENCE
    EVENT_FACTORY = staticmethod(_response_event)
    FORM = staticmethod(form_incidence)

    @staticmethod
    def VERIFY(events, certificate):
        from .response_incidence_check import verify
        return verify(events, certificate)

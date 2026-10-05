"""Source-owned physical port classes gated by their original frame crystals.

Port response topology and raw path organization are distinct TGI operators.
This cycle binds their common raw experience without requiring a text-pattern
organization to exist for a physical sensor class.
"""
import copy
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from .frame_engine import canonical, unique_object
from .identity import REGISTRY_ID, decode
from .local_edit_transport_classes import OwnedPortClasses, _event
from .local_edit_transport_classes_check import verify as verify_classes
from .causal_port_classes import (CausalPortClasses, ResponseIncidenceClasses,
                                  _event as _causal_event, _response_event)
from .causal_port_classes_check import verify as verify_causal_classes
from .response_incidence_check import verify as verify_response_incidence
from .organization import RawOrganization

REVISION = 'TGI-PHASE-BOUND-PORT-CLASSES-V1'


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _source(event_source, port):
    return canonical([event_source, port])


def _fork_crystals(parent):
    if type(parent) is not RawOrganization or parent.frames._pending:
        raise ValueError('Complete predecessor crystal state required')
    child = RawOrganization()
    for name in ('_atoms', '_bonds', '_origins', '_contexts', '_sources', '_pending'):
        setattr(child.frames, name, dict(getattr(parent.frames, name)))
    child.episodes = dict(parent.episodes)
    return child


class PhaseBoundPortClasses:
    REVISION = REVISION
    CLASS_TYPE = OwnedPortClasses
    EVENT_FACTORY = staticmethod(_event)
    VERIFY_CLASS = staticmethod(verify_classes)

    def __init__(self, events=(), *, max_search_steps=100000):
        if type(events) not in (list, tuple) or type(max_search_steps) is not int or max_search_steps < 1:
            raise ValueError('Ordered raw events and positive search budget required')
        rows = copy.deepcopy(list(events))
        native_events = []
        model = RawOrganization()
        seen = set()
        for event in rows:
            if type(event) is not dict or set(event) != {'source', 'action', 'ports'}:
                raise ValueError('Original event source, action and port frames required')
            source, action, ports = event['source'], event['action'], event['ports']
            if type(source) is not str or not source or source in seen or type(ports) is not dict:
                raise ValueError('Unique original event source and port map required')
            seen.add(source)
            native_events.append(self.EVENT_FACTORY(source, action, ports))
            for port, pair in sorted(ports.items()):
                model.observe(_source(source, port), list(pair))
        if len(model.episodes) > max_search_steps:
            raise ValueError('INCOMPLETE: source verification budget exhausted')
        classes = self.CLASS_TYPE(native_events)
        if not all(model._alive(source) for source in model.episodes):
            raise ValueError('Original frame crystal is not alive')
        self._events, self._classes, self._model = rows, classes, model
        self._events_digest = _sha(canonical(rows).encode('utf8'))
        self._class_digest = _sha(canonical(classes._certificate).encode('utf8'))
        self.max_search_steps = max_search_steps

    def _certificate(self):
        class_certificate = self._classes._certificate
        if _sha(canonical(self._events).encode('utf8')) != self._events_digest or \
           _sha(canonical(class_certificate).encode('utf8')) != self._class_digest:
            raise ValueError('Original action, port event, or class certificate changed')
        if not self.VERIFY_CLASS(class_certificate['events'], class_certificate):
            raise ValueError('Original class decision failed independent replay')
        expected_sources = {_source(event['source'], port)
                            for event in self._events for port in event['ports']}
        expected_frames = {canonical([source, index]) for source in expected_sources
                           for index in range(2)}
        if (set(self._model.episodes) != expected_sources or
                set(self._model.frames._sources) != expected_frames or
                self._model.frames._pending):
            raise ValueError('Crystal source inventory differs from original ports')
        if len(expected_sources) > self.max_search_steps:
            raise ValueError('INCOMPLETE: source verification budget exhausted')
        # Port response topology does not require a text-pattern organization.
        # _alive independently checks each original C/L receipt, Ω, ξ, atom,
        # coordinate, forward bond, and exact NMU traversal before use.
        bindings = []
        for event in self._events:
            for port, pair in sorted(event['ports'].items()):
                source = _source(event['source'], port)
                if source not in self._model.episodes or not self._model._alive(source):
                    raise ValueError('Original crystal source is not alive')
                frames, receipts = self._model.episodes[source]
                if tuple(map(decode, frames)) != tuple(pair):
                    raise ValueError('Port observation disagrees with source crystal')
                bindings.append({'source': source, 'event_source': event['source'],
                                 'port': port, 'receipts': [r.as_dict() for r in receipts]})
        return {'revision': self.REVISION, 'registry': REGISTRY_ID,
                'class_certificate': class_certificate,
                'bindings': bindings, 'decision': class_certificate['result']}

    @property
    def certificate(self):
        return copy.deepcopy(self._certificate())

    def observe(self, source, action, ports):
        self._certificate()
        row = {'source': source, 'action': action, 'ports': copy.deepcopy(ports)}
        self.EVENT_FACTORY(source, action, row['ports'])
        if any(event['source'] == source for event in self._events):
            raise ValueError('Duplicate original event source')
        classes = self._classes.observe(source, action, row['ports'])
        model = _fork_crystals(self._model)
        for port, pair in sorted(row['ports'].items()):
            model.observe(_source(source, port), list(pair))
        child = object.__new__(type(self))
        child._events = copy.deepcopy(self._events) + [row]
        child._classes, child._model = classes, model
        child._events_digest = _sha(canonical(child._events).encode('utf8'))
        child._class_digest = _sha(canonical(classes._certificate).encode('utf8'))
        child.max_search_steps = self.max_search_steps
        child._certificate()
        return child

    def observe_batch(self, events):
        """Publish one atomic successor while preserving every ordered event phase."""
        self._certificate()  # Reject altered predecessor before successor creation.
        if type(events) not in (list, tuple) or not events:
            raise ValueError('Nonempty ordered event batch required')
        return type(self)(self._events + copy.deepcopy(list(events)),
                          max_search_steps=self.max_search_steps)

    def resolve(self, action):
        certificate = self._certificate()
        return self._classes.resolve(action) if certificate['decision']['status'] == 'CRYSTAL' else None

    def commit(self, path):
        certificate = self._certificate()
        payload = {'revision': self.REVISION, 'registry': REGISTRY_ID,
                   'events': self._events, 'certificate': certificate}
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
    def recover(cls, path, expected_sha256, *, max_search_steps=100000):
        if type(expected_sha256) is not str or re.fullmatch('[0-9a-f]{64}', expected_sha256) is None:
            raise ValueError('External checkpoint digest required')
        data = Path(path).read_bytes()
        if _sha(data) != expected_sha256:
            raise ValueError('Checkpoint digest mismatch')
        envelope = json.loads(data.decode('utf8'), object_pairs_hook=unique_object)
        if type(envelope) is not dict or set(envelope) != {'payload', 'sha256'}:
            raise ValueError('Invalid checkpoint envelope')
        payload = envelope['payload']
        if (type(payload) is not dict or set(payload) != {'revision', 'registry', 'events', 'certificate'} or
                payload['revision'] != cls.REVISION or payload['registry'] != REGISTRY_ID or
                envelope['sha256'] != _sha(canonical(payload).encode('utf8'))):
            raise ValueError('Invalid checkpoint payload')
        result = cls(payload['events'], max_search_steps=max_search_steps)
        if canonical(result.certificate) != canonical(payload['certificate']):
            raise ValueError('Recomputed source binding differs')
        return result


class PhaseBoundCausalPortClasses(PhaseBoundPortClasses):
    """Alphabet-invariant response topology with the same source crystal law."""
    REVISION = 'TGI-PHASE-BOUND-CAUSAL-PORT-CLASSES-V1'
    CLASS_TYPE = CausalPortClasses
    EVENT_FACTORY = staticmethod(_causal_event)
    VERIFY_CLASS = staticmethod(verify_causal_classes)


class PhaseBoundResponseIncidenceClasses(PhaseBoundPortClasses):
    """Multi-NMU sensor response incidence with original frame crystals."""
    REVISION = 'TGI-PHASE-BOUND-RESPONSE-INCIDENCE-V1'
    CLASS_TYPE = ResponseIncidenceClasses
    EVENT_FACTORY = staticmethod(_response_event)
    VERIFY_CLASS = staticmethod(verify_response_incidence)

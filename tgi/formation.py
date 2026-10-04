"""Experimental causal recurrence chart. Not semantic geometry or MULTIPITA.

Formula, predicted collisions, and falsifiers: contracts/CAUSAL_FORMATION_V1.md.
"""
from dataclasses import dataclass
import json
from .events import Event
from .geometry import Bond, CrystalGeometry, ZERO, add


@dataclass(frozen=True)
class RecurrenceWitness:
    lag: int
    predecessor: Event | None
    matches: bool | None


@dataclass(frozen=True)
class FormationRecord:
    event: Event
    coordinate: tuple[int, ...]
    displacement: tuple[int, ...]
    witnesses: tuple[RecurrenceWitness, ...]
    bond_key: str | None


class CausalFormation:
    def __init__(self):
        self._next = {}
        self._history = {}
        self._coordinates = {}
        self._records = {}
        self._geometry = CrystalGeometry()

    def records(self, stream_id=None):
        return tuple(record for key, record in sorted(self._records.items())
                     if stream_id is None or key[0] == stream_id)

    def geometry_snapshot(self):
        return self._geometry.snapshot()

    def observe(self, events: tuple[Event, ...]) -> tuple[FormationRecord, ...]:
        if not isinstance(events, tuple):
            raise TypeError("A batch must be an immutable tuple of NMU events")
        positions = self._next.copy()
        for event in events:
            if not isinstance(event, Event):
                raise TypeError("Expected validated NMU events")
            expected = positions.get(event.stream_id, 0)
            if event.position != expected:
                raise ValueError("Event gap, replay, or out-of-order occurrence")
            positions[event.stream_id] = expected + 1
        # All domain failures are rejected before state is changed.
        emitted = []
        for event in events:
            history = self._history.get(event.stream_id, ())
            witnesses = tuple(RecurrenceWitness(k, history[-k] if len(history) >= k else None,
                                               history[-k].identity == event.identity if len(history) >= k else None)
                              for k in range(1, 5))
            delta = (1, *(int(w.matches is True) for w in witnesses)) if history else ZERO
            coordinate = add(self._coordinates.get(event.stream_id, ZERO), delta)
            key = None
            if history:
                key = json.dumps(["causal-v1", event.stream_id, event.position], ensure_ascii=True, separators=(",", ":"))
                cert = self._geometry.propose(Bond(key, history[-1], event, delta))
                if cert is not None:
                    raise RuntimeError("An occurrence chain must not fabricate a closure")
            record = FormationRecord(event, coordinate, delta, witnesses, key)
            self._records[(event.stream_id,event.position)] = record
            self._history[event.stream_id] = (history + (event,))[-4:]
            self._coordinates[event.stream_id] = coordinate
            self._next[event.stream_id] = event.position + 1
            emitted.append(record)
        return tuple(emitted)

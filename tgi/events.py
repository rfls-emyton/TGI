"""Occurrences retain a static identity and an independent causal position."""
from dataclasses import dataclass
from .identity import encode, validate_identity


@dataclass(frozen=True, slots=True)
class Event:
    stream_id: str
    position: int
    identity: int

    def __post_init__(self):
        if not isinstance(self.stream_id, str) or not self.stream_id:
            raise ValueError("A stream requires a nonempty provenance identifier")
        if type(self.position) is not int or self.position < 0:
            raise ValueError("Position must be a nonnegative integer")
        validate_identity(self.identity)


class EventStream:
    def __init__(self, stream_id: str):
        if not isinstance(stream_id, str) or not stream_id:
            raise ValueError("A stream requires a nonempty provenance identifier")
        self._stream_id = stream_id
        self._position = 0

    @property
    def position(self) -> int:
        return self._position

    def feed(self, text: str) -> tuple[Event, ...]:
        identities = encode(text)  # Validate the complete chunk before advancing state.
        events = tuple(Event(self._stream_id, self._position + i, identity)
                       for i, identity in enumerate(identities))
        self._position += len(events)
        return events

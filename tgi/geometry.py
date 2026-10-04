"""Exact 5D displacement closure candidate; not a semantic learner.

See contracts/GEOMETRIC_CLOSURE_V1.md. Path search is a neutral constraint solver.
"""
from collections import deque
from dataclasses import dataclass
from .events import Event

ZERO = (0, 0, 0, 0, 0)


def vector(value):
    if not isinstance(value, tuple) or len(value) != 5 or any(type(x) is not int for x in value):
        raise ValueError("Displacement must be a tuple of five exact integers")
    return value


def add(a, b):
    return tuple(x+y for x, y in zip(a, b))


def neg(a):
    return tuple(-x for x in a)


@dataclass(frozen=True)
class Bond:
    key: str
    start: Event
    end: Event
    displacement: tuple[int, ...]

    def __post_init__(self):
        if not isinstance(self.key, str) or not self.key.strip():
            raise ValueError("Bond needs a nonempty provenance key")
        if not isinstance(self.start, Event) or not isinstance(self.end, Event):
            raise TypeError("Endpoints must be NMU events")
        if self.start == self.end:
            raise ValueError("Self loops cannot certify closure")
        vector(self.displacement)


@dataclass(frozen=True)
class Closure:
    proposed: str
    path: tuple[tuple[str, int], ...]
    implied: tuple[int, ...]
    supplied: tuple[int, ...]

    @property
    def residual(self):
        return add(self.implied, neg(self.supplied))


class InconsistentGeometry(ValueError):
    def __init__(self, witness):
        super().__init__("Nonzero cycle displacement")
        self.witness = witness


class CrystalGeometry:
    def __init__(self):
        self._bonds = {}
        self._nodes = {}
        self._adj = {}
        self._closures = []
        self._closed = set()

    def snapshot(self):
        """Immutable, deterministic inspection; no mutable internals escape."""
        return (tuple(sorted(self._bonds.values(), key=lambda b: b.key)),
                tuple(self._closures), tuple(sorted(self._closed)))

    def phase(self, key):
        if key not in self._bonds:
            raise KeyError(key)
        return "STRUCTURALLY_CLOSED" if key in self._closed else "FLUID"

    def _path(self, start, end):
        if start not in self._adj or end not in self._adj:
            return None
        queue = deque([(start, ZERO, ())])
        seen = {start}
        while queue:
            node, displacement, path = queue.popleft()
            if node == end:
                return displacement, path
            for neighbor, key, sign in sorted(self._adj.get(node, ()), key=lambda row: row[1]):
                if neighbor in seen:
                    continue
                seen.add(neighbor)
                delta = self._bonds[key].displacement
                queue.append((neighbor, add(displacement, delta if sign == 1 else neg(delta)),
                              path + ((key, sign),)))
        return None

    def propose(self, bond):
        if not isinstance(bond, Bond):
            raise TypeError("Expected Bond")
        if bond.key in self._bonds:
            raise ValueError("Duplicate provenance key")
        for node in (bond.start, bond.end):
            old = self._nodes.get((node.stream_id, node.position))
            if old is not None and old != node:
                raise ValueError("An event address cannot change identity")
        if (bond.start.stream_id, bond.start.position) == (bond.end.stream_id, bond.end.position):
            raise ValueError("Endpoints share one event address")
        if any(neighbor == bond.end for neighbor, _, _ in self._adj.get(bond.start, ())):
            raise ValueError("Parallel/replayed relation cannot supply independent closure")
        found = self._path(bond.start, bond.end)
        certificate = None
        if found is not None:
            implied, path = found
            certificate = Closure(bond.key, path, implied, bond.displacement)
            if certificate.residual != ZERO:
                raise InconsistentGeometry(certificate)
        # Every rejection above occurs before mutation.
        self._bonds[bond.key] = bond
        for node in (bond.start, bond.end):
            self._nodes[(node.stream_id, node.position)] = node
        self._adj.setdefault(bond.start, []).append((bond.end, bond.key, 1))
        self._adj.setdefault(bond.end, []).append((bond.start, bond.key, -1))
        if certificate is not None:
            self._closures.append(certificate)
            self._closed.update(key for key, _ in certificate.path)
            self._closed.add(bond.key)
        return certificate

    def verify(self, certificate):
        """Recompute a registered closure from actual bonds and oriented endpoints."""
        if certificate not in self._closures:
            return False
        proposed = self._bonds[certificate.proposed]
        node, total = proposed.start, ZERO
        for key, sign in certificate.path:
            bond = self._bonds[key]
            start, end = (bond.start, bond.end) if sign == 1 else (bond.end, bond.start)
            if node != start:
                return False
            total = add(total, bond.displacement if sign == 1 else neg(bond.displacement))
            node = end
        return (node == proposed.end and total == certificate.implied ==
                certificate.supplied == proposed.displacement)

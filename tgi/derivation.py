"""Interface for independently implemented TGI descendants.

A contract declaration is not a mechanism audit or admission certificate.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from .events import Event
from .identity import decode


@dataclass(frozen=True)
class DerivationContract:
    name: str
    revision: str
    purpose: str
    inherited_principles: str
    formation_law: str
    geometry_and_bonding_law: str
    resolution_law: str
    falsifiers: tuple[str, ...]

    def __post_init__(self):
        for field in (self.name, self.revision, self.purpose, self.inherited_principles,
                      self.formation_law, self.geometry_and_bonding_law, self.resolution_law):
            if not isinstance(field, str) or not field.strip():
                raise ValueError("A derivation must state its complete working contract")
        if not isinstance(self.falsifiers, tuple) or not self.falsifiers or any(
                not isinstance(f, str) or not f.strip() for f in self.falsifiers):
            raise ValueError("Explicit falsifiers are required")


class ResolutionStatus(str, Enum):
    RESOLVED = "resolved"
    NO_PATH = "no_path"
    AMBIGUOUS = "ambiguous"
    CONFLICT = "conflict"
    INCOMPLETE = "incomplete"


@dataclass(frozen=True)
class Resolution:
    status: ResolutionStatus
    output: tuple[int, ...] = ()
    evidence: tuple[str, ...] = ()

    def __post_init__(self):
        if not isinstance(self.status, ResolutionStatus):
            raise TypeError("Unknown resolution status")
        if not isinstance(self.output, tuple) or not isinstance(self.evidence, tuple):
            raise TypeError("Output and evidence must be immutable tuples")
        decode(self.output)
        if any(not isinstance(e, str) or not e.strip() for e in self.evidence):
            raise ValueError("Evidence references must be nonempty strings")
        if self.status is ResolutionStatus.RESOLVED:
            if not self.evidence:
                raise ValueError("Resolved output requires trace references")
        elif self.output:
            raise ValueError("An unresolved result cannot contain a final answer")


class Derivation(ABC):
    @property
    @abstractmethod
    def contract(self) -> DerivationContract:
        """Return the independently specified mechanism contract."""

    @abstractmethod
    def observe(self, events: tuple[Event, ...]) -> None:
        """Form organization through the descendant's derived native mechanism."""

    @abstractmethod
    def resolve(self, query: tuple[Event, ...]) -> Resolution:
        """Resolve using the descendant's own geometric and crystallization laws."""

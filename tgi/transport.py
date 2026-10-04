"""Experimental, witnessed single-path transport learned from paired episodes.

The operator family is explicit. It is not a free-language semantic learner.
"""
from dataclasses import dataclass, asdict
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json, os, tempfile
from .identity import encode, decode, REGISTRY_ID
from .frame_engine import FrameEngine, canonical, unique_object

REVISION = "TGI-PATH-TRANSPORT-V1"
MIN_DISTINCT = 3


@dataclass(frozen=True, order=True)
class Transport:
    before_left: tuple
    before_right: tuple
    after_left: tuple
    after_right: tuple

    def region(self, ids):
        left, right = len(self.before_left), len(self.before_right)
        stop = len(ids) - right
        if stop <= left or ids[:left] != self.before_left:
            return None
        if right and ids[stop:] != self.before_right:
            return None
        return left, stop

    def apply(self, ids):
        region = self.region(ids)
        if region is None:
            return None
        left, stop = region
        return self.after_left + ids[left:stop] + self.after_right


def candidates(before, after):
    """All nonempty contiguous correspondences, with no token boundaries."""
    result = set()
    for i in range(len(before)):
        for j in range(len(after)):
            length = 0
            while i+length < len(before) and j+length < len(after) and before[i+length] == after[j+length]:
                length += 1
                result.add(Transport(before[:i], before[i+length:], after[:j], after[j+length:]))
    return frozenset(result)


@dataclass(frozen=True)
class Experience:
    source_id: str
    context: str
    before: tuple
    after: tuple
    before_anchor: int
    after_anchor: int


@dataclass(frozen=True)
class Relation:
    hypotheses: frozenset
    sources: tuple
    distinct_before: frozenset

    @property
    def omega(self):
        return min(Fraction(1), Fraction(len(self.distinct_before), MIN_DISTINCT))

    @property
    def status(self):
        if not self.hypotheses:
            return "CONFLICT"
        if self.omega < 1:
            return "INCOMPLETE"
        if len(self.hypotheses) != 1:
            return "AMBIGUOUS"
        return "SOLID"

    @property
    def xi(self):
        return self.omega if len(self.hypotheses) == 1 else Fraction(0)


@dataclass(frozen=True)
class Witness:
    identity: int
    kind: str
    position: int
    source_id: str = ""
    side: str = ""


@dataclass(frozen=True)
class TransportResult:
    status: str
    text: str | None = None
    witnesses: tuple = ()
    support: tuple = ()
    reason: str = ""


@dataclass(frozen=True)
class CompositionResult:
    status: str
    text: str | None = None
    steps: tuple = ()
    reason: str = ""


class TransportEngine:
    def __init__(self):
        self.frames = FrameEngine()
        self._experiences = {}
        self._relations = {}

    def observe(self, source_id, context, before, after):
        for label, value in (("source_id", source_id), ("context", context)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(label + " must be a nonempty string")
            encode(value)
        a, b = encode(before), encode(after)
        if not a or not b:
            raise ValueError("Paired experiences must be nonempty")
        previous = self._experiences.get(source_id)
        if previous:
            if (previous.context, previous.before, previous.after) != (context, a, b):
                raise ValueError("Source IDs are immutable")
            return self.inspect(context)
        relation = self._relations.get(context)
        possible = (candidates(a, b) if relation is None else
                    frozenset(h for h in relation.hypotheses if h.apply(a) == b))
        # Validate both complete raw streams before exposing either to learning.
        first = self.frames.ingest(before, canonical([source_id, "before"]))
        second = self.frames.ingest(after, canonical([source_id, "after"]))
        experience = Experience(source_id, context, a, b, first.anchor, second.anchor)
        self._experiences[source_id] = experience
        old_sources = () if relation is None else relation.sources
        old_inputs = frozenset() if relation is None else relation.distinct_before
        self._relations[context] = Relation(possible, old_sources+(source_id,), old_inputs|{a})
        return self.inspect(context)

    def inspect(self, context):
        relation = self._relations.get(context)
        if relation is None:
            return {"status": "NO_PATH", "context": context, "candidate_count": 0}
        anchor = None
        if len(relation.hypotheses) == 1:
            anchor = asdict(next(iter(relation.hypotheses)))
        return {"status": relation.status, "context": context,
                "omega": str(relation.omega), "xi": str(relation.xi),
                "candidate_count": len(relation.hypotheses),
                "distinct_inputs": len(relation.distinct_before),
                "support": relation.sources, "relational_anchor": anchor,
                "scope": "single_contiguous_path_transport"}

    def _read(self, experience, side):
        ids = getattr(experience, side)
        anchor = getattr(experience, side+"_anchor")
        result = self.frames.resolve(decode(ids[:1]), anchor)
        if result.status != "RESOLVED" or result.identities != ids:
            return None
        return result.identities

    def resolve(self, context, text):
        ids = encode(text)
        relation = self._relations.get(context)
        if relation is None:
            return TransportResult("NO_PATH", reason="Unobserved relation context")
        if relation.status != "SOLID":
            return TransportResult(relation.status, reason="Relation is not uniquely crystallized")
        operator = next(iter(relation.hypotheses))
        for source in relation.sources:
            exp = self._experiences[source]
            a, b = self._read(exp, "before"), self._read(exp, "after")
            if a is None or b is None or operator.apply(a) != b:
                return TransportResult("INCOMPLETE", reason="Supporting crystal is disconnected or inconsistent")
        region = operator.region(ids)
        if region is None:
            return TransportResult("NO_PATH", reason="Query does not satisfy learned boundary paths")
        first = self._experiences[relation.sources[0]]
        left, stop = region
        witnesses = []
        for i, identity in enumerate(operator.after_left):
            witnesses.append(Witness(identity, "experience", i, first.source_id, "after"))
        for i in range(left, stop):
            witnesses.append(Witness(ids[i], "query", i))
        tail_start = len(first.after)-len(operator.after_right)
        for i, identity in enumerate(operator.after_right):
            witnesses.append(Witness(identity, "experience", tail_start+i, first.source_id, "after"))
        return TransportResult("RESOLVED", decode(w.identity for w in witnesses), tuple(witnesses), relation.sources)

    def compose(self, contexts, text):
        if not isinstance(contexts, (tuple, list)) or not contexts:
            raise ValueError("Composition requires an explicit nonempty context path")
        encode(text)
        steps = []
        current = text
        for context in contexts:
            result = self.resolve(context, current)
            steps.append(result)
            if result.status != "RESOLVED":
                return CompositionResult(result.status, steps=tuple(steps), reason="Composition stopped before completion")
            current = result.text
        return CompositionResult("RESOLVED", current, tuple(steps))

    def save(self, path):
        payload = {"revision": REVISION, "registry": REGISTRY_ID,
                   "experiences": [{"source_id": e.source_id, "context": e.context,
                                    "before": decode(e.before), "after": decode(e.after)}
                                   for e in self._experiences.values()]}
        envelope = {"payload": payload, "sha256": sha256(canonical(payload).encode()).hexdigest()}
        path = Path(path)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf8", dir=path.parent,
                                             prefix=path.name+".", suffix=".tmp", delete=False) as handle:
                temporary = handle.name
                json.dump(envelope, handle, ensure_ascii=True, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if temporary and Path(temporary).exists():
                Path(temporary).unlink()

    @classmethod
    def load(cls, path):
        obj = json.loads(Path(path).read_text(encoding="utf8"), object_pairs_hook=unique_object)
        if not isinstance(obj, dict) or set(obj) != {"payload", "sha256"}:
            raise ValueError("Invalid checkpoint envelope")
        payload = obj["payload"]
        if sha256(canonical(payload).encode()).hexdigest() != obj["sha256"]:
            raise ValueError("Checkpoint checksum mismatch")
        if not isinstance(payload, dict) or set(payload) != {"revision", "registry", "experiences"}:
            raise ValueError("Invalid payload")
        if payload["revision"] != REVISION or payload["registry"] != REGISTRY_ID or not isinstance(payload["experiences"], list):
            raise ValueError("Incompatible transport contract")
        engine = cls()
        for row in payload["experiences"]:
            if not isinstance(row, dict) or set(row) != {"source_id", "context", "before", "after"}:
                raise ValueError("Invalid experience schema")
            if not isinstance(row["source_id"], str) or row["source_id"] in engine._experiences:
                raise ValueError("Duplicate or invalid source ID")
            engine.observe(**row)
        return engine


def verify_certificate(engine, context, query, result):
    """Check sources and every emitted identity without invoking resolve()."""
    if result.status != "RESOLVED" or result.text is None:
        return False
    relation = engine._relations.get(context)
    if relation is None or relation.status != "SOLID" or result.support != relation.sources:
        return False
    operator = next(iter(relation.hypotheses))
    for source in result.support:
        exp = engine._experiences.get(source)
        if exp is None:
            return False
        a, b = engine._read(exp, "before"), engine._read(exp, "after")
        if a is None or b is None or operator.apply(a) != b:
            return False
    ids = encode(query)
    expected = operator.apply(ids)
    if expected is None or encode(result.text) != expected or len(result.witnesses) != len(expected):
        return False
    region = operator.region(ids)
    left, stop = region
    first = engine._experiences[result.support[0]]
    origins = ([('experience', i, first.source_id, 'after') for i in range(len(operator.after_left))]
               + [('query', i, '', '') for i in range(left, stop)]
               + [('experience', i, first.source_id, 'after')
                  for i in range(len(first.after)-len(operator.after_right), len(first.after))])
    for w, identity, origin in zip(result.witnesses, expected, origins):
        if (w.kind, w.position, w.source_id, w.side) != origin:
            return False
        if type(w.position) is not int or w.position < 0 or w.identity != identity:
            return False
        if w.kind == "query":
            if w.source_id or w.side or w.position >= len(ids) or ids[w.position] != identity:
                return False
        elif w.kind == "experience":
            if w.source_id not in result.support or w.side not in ("before", "after"):
                return False
            source = engine._read(engine._experiences[w.source_id], w.side)
            if source is None or w.position >= len(source) or source[w.position] != identity:
                return False
        else:
            return False
    return True

"""Grounded character-span relations. Grammar is induced from demonstrations."""
from dataclasses import dataclass
from itertools import product
from .identity import encode, decode
from .frame_engine import FrameEngine


def label(value):
    if not isinstance(value, str) or not value:
        raise ValueError("Nonempty NMU text required")
    encode(value)
    return value


class EvidenceStore:
    def __init__(self):
        self.frames = FrameEngine()
        self.records = {}

    def add(self, source_id, raw):
        label(source_id); label(raw)
        if source_id in self.records:
            if self.records[source_id][0] != raw:
                raise ValueError("Immutable source changed")
            return
        receipt = self.frames.ingest(raw, source_id)
        self.records[source_id] = (raw, receipt.anchor)

    def alive(self, source_id):
        record = self.records.get(source_id)
        if record is None:
            return False
        raw, anchor = record
        result = self.frames.resolve(raw[0], anchor)
        return result.status == "RESOLVED" and result.identities == encode(raw)


@dataclass(frozen=True)
class Pattern:
    parts: tuple

    def matches(self, raw):
        ids = encode(raw)
        matches = []
        def visit(index, position, ports):
            if index == len(self.parts):
                if position == len(ids):
                    matches.append(dict(ports))
                return
            part = self.parts[index]
            if isinstance(part, tuple):
                if ids[position:position+len(part)] == part:
                    visit(index+1, position+len(part), ports)
            else:
                for stop in range(position+1, len(ids)+1):
                    ports[part] = (position, stop)
                    visit(index+1, stop, ports)
                ports.pop(part, None)
        visit(0, 0, {})
        return matches


def pattern_from_grounding(raw, ports):
    ids = encode(label(raw))
    if not isinstance(ports, dict) or not ports or not set(ports) <= {"subject", "object"}:
        raise ValueError("Grounding requires subject/object ports")
    roles = sorted(ports)
    choices = []
    for role in roles:
        needle = encode(label(ports[role]))
        positions = [(i, i+len(needle)) for i in range(len(ids)-len(needle)+1) if ids[i:i+len(needle)] == needle]
        if not positions:
            raise ValueError("Grounded referent is absent from raw stream")
        choices.append(positions)
    placements = []
    for locations in product(*choices):
        ordered = sorted((start, stop, role) for role, (start, stop) in zip(roles, locations))
        if all(ordered[i][1] <= ordered[i+1][0] for i in range(len(ordered)-1)):
            placements.append(ordered)
    if len(placements) != 1:
        raise ValueError("Grounded span placement is ambiguous")
    parts, position = [], 0
    for start, stop, role in placements[0]:
        parts.extend((ids[position:start], role))
        position = stop
    parts.append(ids[position:])
    return Pattern(tuple(parts))


@dataclass(frozen=True)
class Schema:
    pattern: Pattern
    kind: str
    predicate: str
    polarity: int
    quantifier: str


@dataclass(frozen=True)
class Assertion:
    source_id: str
    predicate: str
    subject: str
    object: str
    polarity: int
    quantifier: str
    world: str
    spans: tuple
    demonstrations: tuple


class GroundedRelations:
    def __init__(self, store=None):
        self.store = store if store is not None else EvidenceStore()
        self.schemas = {}
        self.demonstrations = {}
        self.assertions = {}

    def teach(self, source_id, raw, predicate, ports, kind="fact", polarity=1, quantifier="one"):
        label(source_id); label(predicate)
        if kind not in ("fact", "query") or type(polarity) is not int or polarity not in (-1, 1) or quantifier not in ("one", "all"):
            raise ValueError("Invalid grounded schema metadata")
        pattern = pattern_from_grounding(raw, ports)
        if (kind == "fact" and set(ports) != {"subject", "object"}) or (kind == "query" and len(ports) != 1):
            raise ValueError("Facts require two roles; queries bind exactly one")
        schema = Schema(pattern, kind, predicate, polarity, quantifier)
        signature = (raw, schema, tuple(sorted(ports.items())))
        if source_id in self.demonstrations:
            if self.demonstrations[source_id] != signature:
                raise ValueError("Immutable demonstration changed")
            return self.inspect()
        if source_id in self.store.records:
            raise ValueError("Source ID already belongs to another observation")
        self.store.add(source_id, raw)
        self.demonstrations[source_id] = signature
        self.schemas.setdefault(schema, {})[source_id] = tuple(sorted(ports.items()))
        return self.inspect()

    def inspect(self):
        return {"schemas": len(self.schemas),
                "solid_schemas": sum(len(set(v.values())) >= 3 for v in self.schemas.values()),
                "assertions": len(self.assertions), "demonstrations": len(self.demonstrations)}

    def _parse(self, raw, kind):
        label(raw)
        interpretations = {}
        broken = False
        for schema, support in self.schemas.items():
            if schema.kind != kind or len(set(support.values())) < 3:
                continue
            for ports in schema.pattern.matches(raw):
                if not all(self.store.alive(s) for s in support):
                    broken = True
                    continue
                values = tuple(sorted((role, raw[start:stop]) for role, (start, stop) in ports.items()))
                key = (schema.predicate, schema.polarity, schema.quantifier, values)
                interpretations.setdefault(key, (schema, ports, tuple(support)))
        if broken:
            return "INCOMPLETE", None
        if not interpretations:
            return "NO_PATH", None
        if len(interpretations) != 1:
            return "AMBIGUOUS", None
        return "RESOLVED", next(iter(interpretations.values()))

    def ingest(self, source_id, raw, world="default"):
        label(source_id); label(world)
        if source_id in self.assertions:
            old = self.assertions[source_id]
            if self.store.records[source_id][0] != raw or old.world != world:
                raise ValueError("Immutable assertion changed")
            return {"status": "RESOLVED", "source_id": source_id}
        if source_id in self.store.records:
            raise ValueError("Source ID already in use")
        status, parsed = self._parse(raw, "fact")
        if parsed is None:
            return {"status": status, "source_id": None}
        schema, ports, demonstrations = parsed
        self.store.add(source_id, raw)
        values = {role: raw[start:stop] for role, (start, stop) in ports.items()}
        assertion = Assertion(source_id, schema.predicate, values["subject"], values["object"],
                              schema.polarity, schema.quantifier, world,
                              tuple(sorted((role, start, stop) for role, (start, stop) in ports.items())), demonstrations)
        self.assertions[source_id] = assertion
        return {"status": "RESOLVED", "source_id": source_id}

    def _valid(self, assertion):
        return self.store.alive(assertion.source_id) and all(self.store.alive(s) for s in assertion.demonstrations)

    def _memberships(self, subject, world):
        paths = {subject: ()}
        queue = [subject]
        broken = False
        conflict = False
        while queue:
            current = queue.pop(0)
            for a in self.assertions.values():
                if a.world != world or a.predicate != "is_a" or a.subject != current or a.polarity != 1 or a.quantifier != "one":
                    continue
                if not self._valid(a):
                    broken = True
                    continue
                negatives = [n for n in self.assertions.values() if n.world == world and n.predicate == "is_a"
                             and n.subject == current and n.object == a.object and n.polarity == -1 and n.quantifier == "one"]
                if negatives:
                    broken |= any(not self._valid(n) for n in negatives)
                    conflict = True
                    continue
                if a.object not in paths:
                    paths[a.object] = paths[current]+(a.source_id,)
                    queue.append(a.object)
        return paths, broken, conflict

    def ask(self, raw, world="default"):
        label(world)
        status, parsed = self._parse(raw, "query")
        if parsed is None:
            return {"status": status, "answers": [], "proofs": []}
        schema, ports, question_support = parsed
        bound_role = next(iter(ports))
        start, stop = ports[bound_role]
        bound = raw[start:stop]
        answer_role = "object" if bound_role == "subject" else "subject"
        broken, conflict = False, False
        matches = {}
        membership_cache = {}
        def membership(subject):
            nonlocal broken, conflict
            if subject not in membership_cache:
                paths, damaged, contradicted = self._memberships(subject, world)
                membership_cache[subject] = paths
                broken |= damaged
                conflict |= contradicted
            return membership_cache[subject]
        for a in self.assertions.values():
            if a.world != world or a.predicate != schema.predicate:
                continue
            applicable = []
            if a.quantifier == "all" and schema.quantifier == "one":
                if bound_role == "subject":
                    paths = membership(bound)
                    if a.subject in paths and paths[a.subject]:
                        applicable.append((a.object, paths[a.subject], a))
                elif a.object == bound:
                    subjects = sorted({m.subject for m in self.assertions.values()
                                       if m.world == world and m.predicate == "is_a" and m.polarity == 1})
                    for subject in subjects:
                        paths = membership(subject)
                        if a.subject in paths and paths[a.subject]:
                            path = paths[a.subject]
                            applicable.append((subject, path, self.assertions[path[0]]))
            elif a.quantifier == schema.quantifier and getattr(a, bound_role) == bound:
                applicable.append((getattr(a, answer_role), (), a))
            if applicable and not self._valid(a):
                broken = True
                continue
            for value, member_path, answer_source in applicable:
                matches.setdefault(value, {}).setdefault(a.polarity, []).append((a, member_path, answer_source))
        conflict |= any(1 in signs and -1 in signs for signs in matches.values())
        if broken or conflict:
            return {"status": "INCOMPLETE" if broken else "CONFLICT", "answers": [], "proofs": []}
        answers, proofs = [], []
        for value, signs in sorted(matches.items()):
            if schema.polarity not in signs:
                continue
            a, path, answer_source = signs[schema.polarity][0]
            span = next((start, stop) for role, start, stop in answer_source.spans if role == answer_role)
            _, anchor = self.store.records[answer_source.source_id]
            view = self.store.frames.view()
            origin = view.origins[anchor]
            coordinates = tuple((origin[0]+i, *origin[1:]) for i in range(*span))
            emitted = decode(view.atoms[coordinate].identity for coordinate in coordinates)
            if emitted != value:
                return {"status": "INCOMPLETE", "answers": [], "proofs": []}
            answers.append(emitted)
            proofs.append({"answer": emitted, "source_id": answer_source.source_id, "span": span,
                           "relation_source_id": a.source_id,
                           "coordinates": coordinates,
                           "membership_sources": path, "fact_demonstrations": a.demonstrations,
                           "query_demonstrations": question_support})
        return {"status": "RESOLVED" if answers else "NO_PATH", "answers": answers, "proofs": proofs}

    def verify(self, raw, result, world="default"):
        from .proofcheck import verify_grounded
        return verify_grounded(self, raw, result, world)

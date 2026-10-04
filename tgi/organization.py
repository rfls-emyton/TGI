"""Experimental organization of co-varying raw crystal paths.

No semantic labels enter this API. See contracts/RAW_ORGANIZATION_V1.md.
Intervals remain ordered NMU occurrences, never replacement identities.
"""
from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
from .frame_engine import FrameEngine, canonical
from .identity import encode, decode, REGISTRY_ID

REVISION = "TGI-RAW-ORGANIZATION-V2"
OMEGA_CRIT = 3


def _replace(frames, needle):
    result, total = [], 0
    for ids in frames:
        parts, literal, i = [], [], 0
        while i < len(ids):
            if ids[i:i+len(needle)] == needle:
                if literal:
                    parts.append(("lit", tuple(literal))); literal = []
                parts.append(("axis", 0)); total += 1; i += len(needle)
            else:
                literal.append(ids[i]); i += 1
        if literal:
            parts.append(("lit", tuple(literal)))
        result.append(tuple(parts))
    return tuple(result), total


def _contrasts(left, right):
    if len(left) != len(right) or len(left) < 2 or left == right:
        return set()
    a, b = next((a, b) for a, b in zip(left, right) if a != b)
    k = 0
    while k < min(len(a), len(b)) and a[k] == b[k]:
        k += 1
    found = set()
    right_replacements = {}
    # Include shared leading characters of the changing path. Choosing only
    # the first differing character would introduce accidental character roles.
    for start in range(k+1):
        for stop in range(max(start+1, k), len(a)+1):
            needle = a[start:stop]
            if not needle:
                continue
            lp, lc = _replace(left, needle)
            if lc < 2 and not (lc == 1 and any(k == "axis" for frame in lp[:-1] for k, _ in frame)):
                continue
            for end in range(max(start+1, k), len(b)+1):
                other = b[start:end]
                if not other or other == needle:
                    continue
                if other not in right_replacements:
                    right_replacements[other] = _replace(right, other)
                rp, rc = right_replacements[other]
                if rc == lc and rp == lp:
                    found.add(lp)
    return found


def _match(pattern, frames):
    """All bindings via lazy explicit DFS, preserving prior result order."""
    from .incremental import ACTIVE_SEARCH_BUDGET
    budget = ACTIVE_SEARCH_BUDGET.get()
    if len(frames) > len(pattern):
        return []
    # Necessary conditions only; every survivor still runs complete DFS.
    for parts, ids in zip(pattern, frames):
        if sum(len(v) if k == "lit" else 1 for k, v in parts) > len(ids):
            return []
        cursor = 0
        for kind, value in parts:
            if kind != "lit" or not value:
                continue
            while cursor+len(value) <= len(ids) and ids[cursor:cursor+len(value)] != value:
                cursor += 1
            if cursor+len(value) > len(ids):
                return []
            cursor += len(value)
    states = [({}, {})]
    for fi, ids in enumerate(frames):
        next_states = []
        parts = pattern[fi]
        # Each remaining axis owns at least one NMU occurrence. A valid split
        # cannot consume occurrences needed by the rest of this frame.
        minimum_suffix = [0] * (len(parts)+1)
        for index in range(len(parts)-1, -1, -1):
            kind, value = parts[index]
            minimum_suffix[index] = minimum_suffix[index+1] + (len(value) if kind == "lit" else 1)
        for bindings, locations in states:
            stack = [(0, 0, bindings, locations, None)]
            while stack:
                if budget is not None:
                    budget.match_step()
                pi, position, bindings, locations, next_stop = stack.pop()
                if pi == len(parts):
                    if position == len(ids):
                        next_states.append((dict(bindings), dict(locations)))
                    continue
                kind, value = parts[pi]
                if kind == "lit":
                    if ids[position:position+len(value)] == value:
                        stack.append((pi+1, position+len(value), bindings, locations, None))
                    continue
                bound = value in bindings
                last_stop = len(ids)-minimum_suffix[pi+1]
                # A terminal axis must consume the complete remaining frame.
                first_stop = len(ids) if pi+1 == len(parts) else position+1
                stop = position+len(bindings[value]) if bound else (first_stop if next_stop is None else next_stop)
                if stop > last_stop or stop <= position:
                    continue
                if not bound and stop < last_stop:
                    stack.append((pi, position, bindings, locations, stop+1))
                segment = ids[position:stop]
                if bound and segment != bindings[value]:
                    continue
                nb = dict(bindings); nb[value] = segment
                nl = dict(locations); nl[(fi, pi)] = (position, stop)
                stack.append((pi+1, stop, nb, nl, None))
        states = next_states
    return states


def _joined(frames, axes):
    occupied = {}
    for axis, spans in enumerate(axes):
        for fi, start, stop in spans:
            for pos in range(start, stop):
                if (fi, pos) in occupied:
                    return None
                occupied[(fi, pos)] = axis
    pattern, renumber = [], {}
    for fi, ids in enumerate(frames):
        parts, literal, pos = [], [], 0
        while pos < len(ids):
            axis = occupied.get((fi, pos))
            if axis is None:
                literal.append(ids[pos]); pos += 1; continue
            if literal:
                parts.append(("lit", tuple(literal))); literal = []
            if axis not in renumber:
                renumber[axis] = len(renumber)
            parts.append(("axis", renumber[axis]))
            # Preserve adjacent occurrences of the same axis as separate spans.
            stop = next(stop for f, start, stop in axes[axis] if f == fi and start == pos)
            pos = stop
        if literal:
            parts.append(("lit", tuple(literal)))
        pattern.append(tuple(parts))
    return tuple(pattern)


@dataclass(frozen=True)
class Organization:
    anchor: str
    pattern: tuple
    supports: tuple
    diversity: tuple

    @property
    def omega(self):
        return min(self.diversity)


class RawOrganization:
    def __init__(self):
        self.frames = FrameEngine()
        self.episodes = {}
        self.organizations = {}
        self.rejected_organizations = {}
        self._dirty = False
        from .incremental import StructuralCache
        self._formation_cache = StructuralCache()
        self.formation_work = {}

    def observe(self, source_id, frames):
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError("Nonempty source ID required")
        encode(source_id)
        if not isinstance(frames, (tuple, list)) or not frames:
            raise ValueError("Episode requires an ordered sequence of raw frames")
        ids = tuple(encode(text) for text in frames)
        if any(not frame for frame in ids):
            raise ValueError("Empty frame is not an experience")
        if source_id in self.episodes:
            if self.episodes[source_id][0] != ids:
                raise ValueError("Immutable episode changed")
            return
        # All user input is checked before publishing any frame. Internal keys
        # are injective JSON pairs; user IDs cannot overwrite another frame.
        receipts = self.frames.ingest_batch((decode(frame), canonical([source_id, i]))
                                           for i, frame in enumerate(ids))
        self.episodes[source_id] = (ids, receipts)
        self._dirty = True

    def _alive(self, source_id):
        from fractions import Fraction
        from .resonance import expected_ownership
        from .spatial import traverse
        try:
            ids, receipts = self.episodes[source_id]
            if not ids or len(ids) != len(receipts):
                return False
            view = self.frames.view()
            for fi, (frame, receipt) in enumerate(zip(ids, receipts)):
                c_counts,l_ownership=expected_ownership(len(frame))
                if (receipt.source_id != canonical([source_id, fi]) or type(receipt.count) is not int
                    or receipt.count != len(frame) or type(receipt.anchor) is not int
                    or not isinstance(receipt.origin,tuple) or len(receipt.origin)!=5
                    or any(type(x) is not int for x in receipt.origin)
                    or receipt.c_counts!=c_counts or any(type(x) is not int for x in receipt.c_counts)
                    or receipt.l_ownership!=l_ownership or any(type(x) is not int for block in receipt.l_ownership for x in block)
                    or any(type(x) not in (int,Fraction) or x!=1 for x in (receipt.omega_min,receipt.xi_min))
                    or view.origins.get(receipt.anchor) != receipt.origin):
                    return False
                result = traverse(view, decode(frame[:1]), receipt.anchor)
                expected_path = tuple((receipt.origin[0]+pos,)+receipt.origin[1:] for pos in range(len(frame)))
                if result.identities != frame or result.path != expected_path:
                    return False
            return True
        except (KeyError, IndexError, TypeError, ValueError, AttributeError):
            return False

    def _phase_valid(self, organization):
        from .phase_evidence import validate_organization
        return validate_organization(self, organization)

    def form(self, *, max_search_steps=None):
        from .incremental import SearchBudget
        budget = SearchBudget(max_search_steps)
        with budget.scope():
            episodes = []
            for sid, (expected, receipts) in sorted(self.episodes.items()):
                # _alive proves both exact crystal paths and receipt ownership.
                # Reuse their verified identities only after that complete check.
                if not self._alive(sid):
                    raise ValueError("Broken crystal or receipt cannot form organization")
                episodes.append((sid, (expected, receipts)))
            cache, work = self._formation_cache.stage((frames for _, (frames, _) in episodes), budget)
            candidates = cache.candidates
            supported = {}
            for pattern in candidates:
                budget.consume()
                matches = [(sid, match) for sid, (frames, _) in episodes
                           if len(frames) == len(pattern) for match in _match(pattern, frames)]
                if len({match[0][0] for _, match in matches}) >= OMEGA_CRIT:
                    supported[pattern] = matches
            joined = set(supported)
            for sid, (frames, _) in episodes:
                axes = set()
                for pattern, matches in supported.items():
                    for source, (_, locations) in matches:
                        if source == sid:
                            axes.add(tuple(sorted((fi, start, stop)
                                                  for (fi, _), (start, stop) in locations.items())))
                axes = sorted(axes)
                joined.update(cache.join(frames, axes, work, budget))
            from .phase_evidence import oppositions
            formed, rejected = {}, {}
            for pattern in sorted(joined):
                budget.consume()
                n = 1+max(v for frame in pattern for k, v in frame if k == "axis")
                values = [set() for _ in range(n)]
                supports = set()
                for sid, (frames, _) in episodes:
                    if len(frames) != len(pattern):
                        continue
                    interpretations = _match(pattern, frames)
                    if len(interpretations) != 1:
                        continue
                    bindings, _ = interpretations[0]
                    supports.add(sid)
                    for axis, value in bindings.items():
                        values[axis].add(value)
                diversity = tuple(len(v) for v in values)
                if min(diversity) >= OMEGA_CRIT:
                    anchor = sha256(canonical(pattern).encode()).hexdigest()
                    organization = Organization(anchor, pattern, tuple(sorted(supports)), diversity)
                    opposing = oppositions(pattern, episodes)
                    if opposing:
                        rejected[anchor] = (organization, opposing)
                    else:
                        formed[anchor] = organization
            report = self._inspection(formed, rejected, work, False)
        self.organizations = formed
        self.rejected_organizations = rejected
        self._formation_cache = cache
        work["search_steps"] = budget.used
        work["matcher_steps"] = budget.matcher_used
        work["budget_revision"] = "TGI-FORMATION-WORK-V3"
        self.formation_work = work
        self._dirty = False
        report["formation_work"] = dict(work)
        return report

    def inspect(self):
        return self._inspection(self.organizations, self.rejected_organizations,
                                getattr(self, "formation_work", {}), self._dirty)

    def _inspection(self, organizations, rejected, work, pending):
        return {"revision": REVISION, "episodes": len(self.episodes),
                "organizations": [{"anchor": h.anchor, "axes": len(h.diversity),
                                    "omega": h.omega, "xi": int(self._phase_valid(h)),
                                    "supports": h.supports}
                                   for _, h in sorted(organizations.items())],
                "revoked": [{"anchor": a, "omega": h.omega, "xi": 0,
                             "opposing_sources": [o.source for o in opposing]}
                            for a, (h, opposing) in sorted(rejected.items())],
                "formation_work": dict(work),
                "pending_formation": pending}

    def resolve(self, prefix, *, terminal_only=False, max_formation_steps=None):
        if not isinstance(prefix, (tuple, list)) or not prefix:
            raise ValueError("Resolution needs an ordered raw frame prefix")
        raw = tuple(encode(text) for text in prefix)
        if any(not frame for frame in raw):
            raise ValueError("Empty trigger frame")
        from .incremental import SearchBudget, FormationSearchLimit
        SearchBudget(max_formation_steps)  # Validate even when already formed.
        if self._dirty:
            try:
                if max_formation_steps is None:
                    self.form()
                else:
                    self.form(max_search_steps=max_formation_steps)
            except FormationSearchLimit as exc:
                return {"status": "INCOMPLETE", "output": [], "candidates": [],
                        "proofs": [], "evidence": [], "revoked_candidates": [],
                        "reason": "formation_search_limit", "search_steps": exc.used}
        outputs, proofs, broken, unbound = set(), [], False, False
        view = self.frames.view()
        for anchor, h in sorted(self.organizations.items()):
            if len(raw) >= len(h.pattern) or (terminal_only and len(h.pattern) != len(raw)+1):
                continue
            for bindings, locations in _match(h.pattern, raw):
                if anchor != h.anchor or not self._phase_valid(h):
                    broken = True; continue
                if len(bindings) != len(h.diversity):
                    unbound = True; continue
                source = h.supports[0]
                source_ids, receipts = self.episodes[source]
                source_binding, _ = _match(h.pattern, source_ids)[0]
                out, trace = [], []
                for fi in range(len(raw), len(h.pattern)):
                    ids, frame_trace, source_offset = [], [], 0
                    for pi, (kind, value) in enumerate(h.pattern[fi]):
                        if kind == "lit":
                            receipt = receipts[fi]
                            for offset in range(len(value)):
                                coord = (receipt.origin[0]+source_offset+offset,)+receipt.origin[1:]
                                atom = view.atoms[coord]
                                ids.append(atom.identity)
                                frame_trace.append({"kind": "crystal", "source": source,
                                                    "frame": fi, "position": source_offset+offset,
                                                    "coordinate": coord})
                            source_offset += len(value)
                        else:
                            pfi, ppi = next(key for key in sorted(locations)
                                           if h.pattern[key[0]][key[1]] == ("axis", value))
                            start, stop = locations[(pfi, ppi)]
                            ids.extend(raw[pfi][start:stop])
                            frame_trace.extend({"kind": "trigger", "frame": pfi, "position": pos}
                                               for pos in range(start, stop))
                            source_offset += len(source_binding[value])
                    out.append(decode(ids)); trace.append(frame_trace)
                outputs.add(tuple(out))
                proofs.append({"anchor": anchor, "output": out, "characters": trace,
                               "supports": h.supports})
        if terminal_only:
            # Preserve every distinct conclusion, but one canonical witness per
            # conclusion is sufficient. The checker independently tests consensus.
            witnesses = {}
            for proof in proofs:
                witnesses.setdefault(tuple(proof["output"]), proof)
            proofs = list(witnesses.values())
        revoked = [a for a, (h, _) in sorted(self.rejected_organizations.items())
                   if len(raw) < len(h.pattern) and (not terminal_only or len(h.pattern) == len(raw)+1)
                   and _match(h.pattern, raw)]
        if broken:
            status = "INCOMPLETE"
        elif len(outputs) > 1 or (outputs and unbound):
            status = "AMBIGUOUS"
        elif outputs:
            status = "RESOLVED"
        elif unbound:
            status = "INCOMPLETE"
        elif revoked:
            status = "AMBIGUOUS"
        else:
            status = "NO_PATH"
        return {"status": status, "output": list(next(iter(outputs))) if status == "RESOLVED" else [],
                "candidates": [list(out) for out in sorted(outputs)], "proofs": proofs,
                "revoked_candidates": revoked}

    def ask(self, raw, *, max_formation_steps=None):
        """Find an observed temporal prefix; query order comes from episodes."""
        encode(raw)
        if not raw:
            raise ValueError("Empty query")
        from .incremental import SearchBudget, FormationSearchLimit
        SearchBudget(max_formation_steps)  # Validate even when already formed.
        if self._dirty:
            try:
                if max_formation_steps is None:
                    self.form()
                else:
                    self.form(max_search_steps=max_formation_steps)
            except FormationSearchLimit as exc:
                return {"status": "INCOMPLETE", "output": [], "candidates": [],
                        "proofs": [], "evidence": [], "revoked_candidates": [],
                        "reason": "formation_search_limit", "search_steps": exc.used}
        hypotheses = list(self.organizations.values()) + [h for h, _ in self.rejected_organizations.values()]
        lengths = {len(h.pattern)-2 for h in hypotheses}
        prefixes = {(): []} if 0 in lengths else {}
        for sid, (frames, _) in self.episodes.items():
            for count in lengths:
                if 0 < count <= len(frames):
                    prefixes.setdefault(tuple(decode(f) for f in frames[:count]), []).append(sid)
        outputs, evidence, uncertain, broken = set(), [], False, False
        for prefix, sources in sorted(prefixes.items()):
            result = self.resolve(prefix+(raw,))
            if result["status"] == "NO_PATH":
                continue
            live = [sid for sid in sources if self._alive(sid)]
            if sources and not live:
                broken = True; continue
            broken |= result["status"] == "INCOMPLETE"
            uncertain |= result["status"] == "AMBIGUOUS"
            if result["status"] == "RESOLVED":
                outputs.add(tuple(result["output"]))
                evidence.append({"prefix": list(prefix), "sources": live, "resolution": result})
        status = ("INCOMPLETE" if broken else "CONFLICT" if len(outputs) > 1 else
                  "AMBIGUOUS" if uncertain else "RESOLVED" if outputs else "NO_PATH")
        return {"status": status, "output": list(next(iter(outputs))) if status == "RESOLVED" else [],
                "candidates": [list(o) for o in sorted(outputs)], "evidence": evidence}

    def save(self, path):
        # Reuse the foundation's atomic publication; no derived semantic labels
        # or externally supplied patterns are accepted on checkpoint loading.
        import os, tempfile
        if not all(self._alive(s) for s in self.episodes):
            raise ValueError("Cannot checkpoint broken crystal evidence")
        payload = {"revision": REVISION, "registry": REGISTRY_ID,
                   "episodes": [{"source_id": sid, "frames": [decode(f) for f in frames]}
                                for sid, (frames, _) in self.episodes.items()]}
        envelope = {"payload": payload, "sha256": sha256(canonical(payload).encode()).hexdigest()}
        path = Path(path); temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf8", dir=path.parent, delete=False) as f:
                temporary = Path(f.name); f.write(canonical(envelope)); f.flush(); os.fsync(f.fileno())
            os.replace(temporary, path)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()

    @classmethod
    def load(cls, path, *, allow_legacy=False, defer_formation=False):
        from .frame_engine import unique_object
        if type(defer_formation) is not bool:
            raise TypeError("defer_formation must be bool")
        envelope = json.loads(Path(path).read_text(encoding="utf8"), object_pairs_hook=unique_object)
        if not isinstance(envelope, dict) or set(envelope) != {"payload", "sha256"}:
            raise ValueError("Invalid raw checkpoint envelope")
        payload = envelope["payload"]
        if (not isinstance(payload, dict) or set(payload) != {"revision", "registry", "episodes"}
            or not isinstance(payload["episodes"], list)):
            raise ValueError("Invalid raw checkpoint payload")
        accepted = {REVISION, "TGI-RAW-ORGANIZATION-V1"} if allow_legacy else {REVISION}
        if (payload["revision"] not in accepted or payload["registry"] != REGISTRY_ID or
            sha256(canonical(payload).encode()).hexdigest() != envelope["sha256"]):
            raise ValueError("Invalid raw organization checkpoint")
        engine = cls()
        for item in payload["episodes"]:
            if set(item) != {"source_id", "frames"} or item["source_id"] in engine.episodes:
                raise ValueError("Invalid or duplicate raw episode")
            engine.observe(item["source_id"], item["frames"])
        if not defer_formation:
            engine.form()
        return engine

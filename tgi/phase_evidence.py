"""Derive lock eligibility from actual supporting and opposing crystal paths."""
from dataclasses import dataclass
from hashlib import sha256
from .frame_engine import canonical


@dataclass(frozen=True)
class Opposition:
    source: str
    observed: tuple
    predicted: tuple
    observed_path: tuple
    first_divergences: tuple


def oppositions(pattern, episodes):
    from .organization import _match
    conflicts = []
    for source, (frames, receipts) in episodes:
        if len(frames) != len(pattern):
            continue
        predicted = set()
        for bindings, _ in _match(pattern, frames[:-1]):
            needed = {v for k, v in pattern[-1] if k == "axis"}
            if not needed <= bindings.keys():
                continue
            predicted.add(tuple(identity for kind, value in pattern[-1]
                                for identity in (value if kind == "lit" else bindings[value])))
        if predicted and frames[-1] not in predicted:
            origin = receipts[-1].origin
            path = tuple((origin[0]+pos,)+origin[1:] for pos in range(len(frames[-1])))
            divergences = []
            for proposed in sorted(predicted):
                pos = next(i for i in range(max(len(proposed), len(frames[-1])))
                           if proposed[i:i+1] != frames[-1][i:i+1])
                divergences.append((pos, proposed[pos] if pos < len(proposed) else None,
                                    frames[-1][pos] if pos < len(frames[-1]) else None))
            conflicts.append(Opposition(source, frames[-1], tuple(sorted(predicted)), path, tuple(divergences)))
    return tuple(conflicts)


def validate_organization(engine, h, *, require_consistent=True):
    """No reliance on declared support counts or on the generating resolver."""
    from .organization import _match, OMEGA_CRIT
    try:
        if h.anchor != sha256(canonical(h.pattern).encode()).hexdigest():
            return False
        n = 1+max(v for frame in h.pattern for k, v in frame if k == "axis")
        values = [set() for _ in range(n)]
        supports = set()
        episodes = sorted(engine.episodes.items())
        for source, (frames, _) in episodes:
            if len(frames) != len(h.pattern):
                continue
            matches = _match(h.pattern, frames)
            if len(matches) == 1:
                if not engine._alive(source):
                    return False
                supports.add(source)
                for axis, value in matches[0][0].items():
                    values[axis].add(value)
        diversity = tuple(len(v) for v in values)
        if (tuple(sorted(supports)) != h.supports or diversity != h.diversity or min(diversity) < OMEGA_CRIT):
            return False
        # Opposing paths are not allowed to disappear merely because they are
        # absent from the positive support list.
        for source, (frames, _) in episodes:
            if len(frames) == len(h.pattern) and _match(h.pattern, frames[:-1]) and not engine._alive(source):
                return False
        return not require_consistent or not oppositions(h.pattern, episodes)
    except (IndexError, KeyError, TypeError, ValueError):
        return False


def blocked_prefix(engine, prefix):
    """Independently establish ambiguity; do not call a generating resolver."""
    from .organization import _match
    from .identity import encode
    raw = tuple(encode(t) for t in prefix)
    outputs, unbound = set(), False
    for h in engine.organizations.values():
        if len(h.pattern) != len(raw)+1:
            continue
        for bindings, _ in _match(h.pattern, raw):
            if not engine._phase_valid(h):
                return False
            if len(bindings) != len(h.diversity):
                unbound = True; continue
            outputs.add(tuple(identity for k, v in h.pattern[-1]
                              for identity in (v if k == "lit" else bindings[v])))
    if len(outputs) > 1 or (outputs and unbound):
        return True
    if outputs or unbound:
        return False
    for h, opposing in engine.rejected_organizations.values():
        if len(h.pattern) == len(raw)+1 and _match(h.pattern, raw):
            if (validate_organization(engine, h, require_consistent=False) and opposing and
                opposing == oppositions(h.pattern, sorted(engine.episodes.items()))):
                return True
    return False

"""Exhaustive full organization inventory checker independent of formation.

Shares discrete contrast, matching and join definitions; does not share the
producer's candidate index, cache, pruning, form, or resolution operations.
"""
from hashlib import sha256
from itertools import combinations
from .frame_engine import canonical
from .organization import Organization, OMEGA_CRIT, _contrasts, _match, _joined
from .organization_snapshot import snapshot
from .phase_evidence import oppositions
from .role_work import RoleSearchBudget
from .compatible_joins import compatible_subsets


def verify_organization_inventory(engine, *, max_search_steps=None):
    # Exhaustion is raised, never interpreted as verified completeness or absence.
    budget = RoleSearchBudget(max_search_steps)
    with budget.scope():
        try:
            original = snapshot(engine)
            if not all(original._alive(s) for s in original.episodes):
                return False
            expected = dict(original.episodes)
            episodes = sorted(expected.items())
            paths = sorted({frames for frames, _ in expected.values() if len(frames)>=2})
            candidates = set()
            for left, right in combinations(paths, 2):
                budget.consume()
                candidates.update(_contrasts(left, right))
            supported = {}
            for pattern in sorted(candidates):
                budget.consume()
                matches = [(s, match) for s, (frames, _) in episodes
                           if len(frames) == len(pattern) for match in _match(pattern, frames)]
                if len({match[0][0] for _, match in matches}) >= OMEGA_CRIT:
                    supported[pattern] = matches
            joined = set(supported)
            # Joins depend only on exact frame identities and interval locations.
            # Repeated sources retain separate support/provenance below, but
            # their identical exhaustive subset enumeration adds no pattern.
            joined_paths = set()
            for source, (frames, _) in episodes:
                if frames in joined_paths:
                    continue
                joined_paths.add(frames)
                axes = sorted({tuple(sorted((fi, start, stop) for (fi, _), (start, stop) in locations.items()))
                               for matches in supported.values() for s, (_, locations) in matches if s == source})
                # Independent interval-conflict enumeration, complete for every
                # subset that can yield a non-overlapping joined pattern.
                for subset in compatible_subsets(axes,budget):
                    pattern = _joined(frames, subset)
                    if pattern is not None:
                        joined.add(pattern)
            active, rejected = {}, {}
            for pattern in sorted(joined):
                budget.consume()
                n = 1+max(v for frame in pattern for k, v in frame if k == 'axis')
                values = [set() for _ in range(n)]
                supports = set()
                for source, (frames, _) in episodes:
                    if len(frames) != len(pattern):
                        continue
                    matches = _match(pattern, frames)
                    if len(matches) != 1:
                        continue
                    supports.add(source)
                    for axis, value in matches[0][0].items():
                        values[axis].add(value)
                diversity = tuple(map(len, values))
                if min(diversity) < OMEGA_CRIT:
                    continue
                anchor = sha256(canonical(pattern).encode()).hexdigest()
                h = Organization(anchor, pattern, tuple(sorted(supports)), diversity)
                opposing = oppositions(pattern, episodes)
                if opposing:
                    rejected[anchor] = (h, opposing)
                else:
                    active[anchor] = h
            return dict(original.organizations) == active and dict(original.rejected_organizations) == rejected
        except (ValueError, TypeError, KeyError, IndexError, AttributeError):
            return False

"""Reusable structural search, never cached semantic admission."""
from dataclasses import dataclass, field
from itertools import combinations
from contextlib import contextmanager
from contextvars import ContextVar

ACTIVE_SEARCH_BUDGET = ContextVar("tgi_formation_search_budget", default=None)


class FormationSearchLimit(RuntimeError):
    def __init__(self, limit, used):
        self.limit, self.used = limit, used
        super().__init__(f'Formation search limit {limit} reached after {used} steps')


class SearchBudget:
    def __init__(self, limit=None):
        if limit is not None and (type(limit) is not int or limit < 0):
            raise ValueError('Search limit must be a nonnegative integer or None')
        self.limit, self.used, self.matcher_used = limit, 0, 0

    @contextmanager
    def scope(self):
        token = ACTIVE_SEARCH_BUDGET.set(self)
        try:
            yield self
        finally:
            ACTIVE_SEARCH_BUDGET.reset(token)

    def match_step(self):
        self.consume()
        self.matcher_used += 1

    def consume(self):
        if self.limit is not None and self.used >= self.limit:
            raise FormationSearchLimit(self.limit, self.used)
        self.used += 1


@dataclass
class StructuralCache:
    seen: frozenset = frozenset()
    candidates: frozenset = frozenset()
    # One current axis signature per distinct episode, not a history of variants.
    joins: dict = field(default_factory=dict)

    buckets: dict = field(default_factory=dict)
    witnesses: dict = field(default_factory=dict)

    def stage(self, episode_paths, budget=None):
        budget = budget if budget is not None else SearchBudget()
        from .organization import _contrasts, _replace
        current = frozenset(paths for paths in episode_paths if len(paths) >= 2)
        reset = not self.seen <= current
        previous = frozenset() if reset else self.seen
        fresh = current-previous
        candidates = set() if reset else set(self.candidates)
        buckets = {} if reset else dict(self.buckets)
        witnesses = {} if reset else dict(self.witnesses)
        touched = set()
        intervals = replacements = 0
        literal_pool = {}
        for frames in sorted(fresh):
            needles = set()
            for ids in frames:
                for start in range(len(ids)):
                    for stop in range(start+1, len(ids)+1):
                        budget.consume(); intervals += 1
                        needle = ids[start:stop]
                        if needle in needles:
                            continue
                        needles.add(needle)
                        budget.consume(); replacements += 1
                        pattern, count = _replace(frames, needle)
                        # Share exact immutable literal tuples only within this stage.
                        pattern = tuple(tuple((kind, literal_pool.setdefault(value, value)
                                               if kind == "lit" else value)
                                              for kind, value in frame) for frame in pattern)
                        if count < 2 and not (count == 1 and any(kind == 'axis' for frame in pattern[:-1] for kind, _ in frame)):
                            continue
                        buckets[pattern] = buckets.get(pattern, frozenset()) | {frames}
                        touched.add(pattern)
        pair_results = {}
        for pattern in sorted(touched-candidates):
            supports = buckets[pattern]
            new = sorted(supports & fresh)
            old = sorted(supports-fresh)
            def pairs():
                for a in new:
                    for b in old:
                        yield tuple(sorted((a,b)))
                yield from combinations(new,2)
            for pair in pairs():
                if pair not in pair_results:
                    budget.consume()
                    pair_results[pair] = _contrasts(*pair)
                if pattern in pair_results[pair]:
                    candidates.add(pattern); witnesses[pattern] = pair
                    break
        staged = StructuralCache(current, frozenset(candidates),
                                 {} if reset else {p: v for p,v in self.joins.items() if p in current},
                                 buckets, witnesses)
        stats = {"contrast_pairs_evaluated": len(pair_results), "new_episode_contents": len(fresh),
                 "cache_reset": reset, "joins_evaluated": 0, "joins_reused": 0, "joins_empty": 0,
                 "intervals_enumerated": intervals, "signature_replacements": replacements,
                 "index_patterns": len(buckets), "index_witnesses": len(witnesses)}
        return staged, stats

    def join(self, frames, axes, stats, budget=None):
        budget = budget if budget is not None else SearchBudget()
        from .organization import _joined
        signature = tuple(axes)
        if not signature:
            self.joins.pop(frames, None)
            stats["joins_empty"] += 1
            return frozenset()
        old = self.joins.get(frames)
        if old is not None and old[0] == signature:
            stats["joins_reused"] += 1
            return old[1]
        found = set()
        def extend(start, chosen):
            for i in range(start, len(axes)):
                budget.consume()
                proposal = chosen+(axes[i],)
                pattern = _joined(frames, proposal)
                if pattern is not None:
                    found.add(pattern)
                    extend(i+1, proposal)
        extend(0, ())
        result = frozenset(found)
        self.joins[frames] = (signature, result)
        stats["joins_evaluated"] += 1
        return result

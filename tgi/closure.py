"""Certified finite closure of organizations formed from raw episodes.

Derived frames are transient consequences, never new formation exposures.
See contracts/RAW_CLOSURE_V2.md for terminal and resource semantics.
"""
from dataclasses import dataclass
from .identity import encode, decode
from .organization import _match


class BudgetExhausted(Exception):
    pass


@dataclass
class Work:
    limit: int
    used: int = 0

    def tick(self):
        self.used += 1
        if self.used > self.limit:
            raise BudgetExhausted


def observations(engine):
    records = []
    for source, (frames, _) in sorted(engine.episodes.items()):
        if not engine._alive(source):
            raise ValueError("Broken observed crystal")
        records.extend({"source": source, "frame": fi, "text": decode(ids)}
                       for fi, ids in enumerate(frames))
    return records


def prefixes(engine, nodes, work):
    """Join ordered input paths only when their repeated axes agree."""
    encoded = {text: encode(text) for text in sorted(nodes)}
    yielded = set()
    input_patterns = set()
    frame_matches = {}
    candidates = dict(engine.organizations)
    candidates.update({a: h for a, (h, _) in engine.rejected_organizations.items()})
    for _, h in sorted(candidates.items()):
        if len(h.pattern) < 2 or h.pattern[:-1] in input_patterns:
            continue
        input_patterns.add(h.pattern[:-1])
        states = [()]
        for part in h.pattern[:-1]:
            candidates = []
            for text, ids in encoded.items():
                work.tick()
                key = (part, ids)
                if key not in frame_matches:
                    frame_matches[key] = bool(_match((part,), (ids,)))
                if frame_matches[key]:
                    candidates.append(text)
            next_states = []
            for state in states:
                for text in candidates:
                    work.tick()
                    proposal = state+(text,)
                    if _match(h.pattern, tuple(encoded[t] for t in proposal)):
                        next_states.append(proposal)
            states = next_states
        for state in states:
            if state not in yielded:
                yielded.add(state)
                yield state


def terminal(engine, text):
    ids = encode(text)
    known = list(engine.organizations.values())+[h for h, _ in engine.rejected_organizations.values()]
    return not any(_match((part,), (ids,)) for h in known
                   for part in h.pattern[:-1] if any(k == "lit" and v for k, v in part))


def query_consequences(query, steps):
    dependent = {query}
    produced = set()
    changed = True
    while changed:
        changed = False
        for step in steps:
            if any(text in dependent for text in step["prefix"]):
                output = step["result"]["output"][0]
                produced.add(output)
                if output not in dependent:
                    dependent.add(output); changed = True
    return produced


def resolve_closure(engine, query, *, max_nodes=1024, max_work=1000000, max_formation_steps=None):
    encode(query)
    if not query:
        raise ValueError("Nonempty query required")
    if type(max_nodes) is not int or type(max_work) is not int or min(max_nodes, max_work) < 1:
        raise ValueError("Resource ceilings must be positive integers")
    from .incremental import SearchBudget, FormationSearchLimit
    SearchBudget(max_formation_steps)
    work = Work(max_work)
    steps, blocked, obs, nodes, fired = [], [], [], set(), set()
    def result(status, reason=None, answers=()):
        return {"status": status, "output": list(answers) if status == "RESOLVED" else [],
                "query": query, "observations": obs, "steps": steps, "blocked": blocked, "node_count": len(nodes),
                "work": work.used, "reason": reason}
    try:
        if engine._dirty:
            if max_formation_steps is None:
                engine.form()
            else:
                engine.form(max_search_steps=max_formation_steps)
        from .organization_snapshot import snapshot
        engine = snapshot(engine)
        obs = observations(engine)
        nodes = {r["text"] for r in obs} | {query}
        if len(nodes) > max_nodes:
            return result("INCOMPLETE", "node_budget")
        while True:
            added = False
            for prefix in prefixes(engine, nodes, work):
                if prefix in fired:
                    continue
                fired.add(prefix)
                resolution = engine.resolve(prefix, terminal_only=True)
                if resolution["status"] in ("AMBIGUOUS", "CONFLICT"):
                    blocked.append({"prefix": list(prefix), "status": resolution["status"]})
                    continue
                if resolution["status"] == "INCOMPLETE":
                    return result("INCOMPLETE", "incomplete_step")
                if resolution["status"] != "RESOLVED" or len(resolution["output"]) != 1:
                    raise ValueError("Matched organization has no unique terminal frame")
                steps.append({"prefix": list(prefix), "result": resolution})
                text = resolution["output"][0]
                if text not in nodes:
                    if len(nodes) == max_nodes:
                        return result("INCOMPLETE", "node_budget")
                    nodes.add(text); added = True
            if not added:
                break
        dependent = {query} | query_consequences(query, steps)
        if any(any(t in dependent for t in b["prefix"]) for b in blocked):
            return result("AMBIGUOUS", "query_dependent_blocked_step")
        consumed = {t for step in steps for t in step["prefix"]}
        ends = sorted(text for text in query_consequences(query, steps)
                      if text not in consumed and terminal(engine, text))
        if len(ends) > 1:
            return result("CONFLICT", "multiple_terminal_consequences")
        return result("RESOLVED", answers=ends) if ends else result("NO_PATH", "no_terminal_consequence")
    except FormationSearchLimit:
        return result("INCOMPLETE", "formation_search_limit")
    except BudgetExhausted:
        return result("INCOMPLETE", "work_budget")
    except ValueError as error:
        return result("INCOMPLETE", str(error))


def verify_closure(engine, query, certificate, *, max_work=1000000):
    """Replay proof and independently require closure; never invoke a resolver."""
    from .organization_check import verify_resolution
    try:
        if engine._dirty or certificate["status"] != "RESOLVED" or certificate["query"] != query:
            return False
        from .organization_snapshot import snapshot
        engine = snapshot(engine)
        obs = observations(engine)
        if certificate["observations"] != obs:
            return False
        available = {r["text"] for r in obs} | {query}
        checked = set()
        for step in certificate["steps"]:
            prefix = tuple(step["prefix"])
            if prefix in checked or not all(t in available for t in prefix):
                return False
            resolution = step["result"]
            if len(resolution["output"]) != 1 or not verify_resolution(engine, prefix, resolution, terminal_only=True):
                return False
            checked.add(prefix)
            available.add(resolution["output"][0])
        # A valid path alone does not certify that conflicting paths were absent.
        # Every applicable ordered prefix in the final state needs a checked step.
        from .phase_evidence import blocked_prefix
        blocked = set()
        for item in certificate["blocked"]:
            prefix = tuple(item["prefix"])
            if (prefix in checked or prefix in blocked or not all(t in available for t in prefix)
                or item["status"] not in ("AMBIGUOUS", "CONFLICT") or not blocked_prefix(engine, prefix)):
                return False
            blocked.add(prefix)
        expected = set(prefixes(engine, available, Work(max_work)))
        if checked | blocked != expected:
            return False
        dependent = {query} | query_consequences(query, certificate["steps"])
        if any(any(t in dependent for t in prefix) for prefix in blocked):
            return False
        consumed = {t for step in certificate["steps"] for t in step["prefix"]}
        ends = sorted(t for t in query_consequences(query, certificate["steps"])
                      if t not in consumed and terminal(engine, t))
        return len(ends) == 1 and certificate["output"] == ends and certificate["node_count"] == len(available)
    except (ValueError, KeyError, TypeError, IndexError, BudgetExhausted):
        return False

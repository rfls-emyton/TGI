"""Controlled paired interventions and goal-directed certified traversal."""
from dataclasses import dataclass
from collections import deque
from itertools import product
from math import prod
from .grounding import EvidenceStore, label
from .frame_engine import canonical


def state_tuple(state):
    if not isinstance(state, dict) or not state:
        raise ValueError("State requires a nonempty sensor mapping")
    for key, value in state.items():
        label(key); label(value)
    return tuple(sorted(state.items()))


@dataclass(frozen=True)
class Trial:
    trial_id: str
    action: str
    before: tuple
    treated: tuple
    control: tuple
    controlled: bool
    condition: str
    world: str


class InterventionRelations:
    def __init__(self, store=None):
        self.store = store if store is not None else EvidenceStore()
        self.trials = {}

    def observe(self, trial_id, action, before, treated_after, control_after=None,
                controlled=False, condition="default", world="default"):
        for value in (trial_id, action, condition, world):
            label(value)
        if type(controlled) is not bool:
            raise ValueError("controlled must be an explicit boolean")
        a, b = state_tuple(before), state_tuple(treated_after)
        c = state_tuple(control_after) if control_after is not None else ()
        keys = tuple(k for k, _ in a)
        if tuple(k for k, _ in b) != keys or (c and tuple(k for k, _ in c) != keys):
            raise ValueError("All measured paths require the same sensor keys")
        if controlled and not c:
            raise ValueError("Controlled trial requires a paired control")
        trial = Trial(trial_id, action, a, b, c, controlled, condition, world)
        if trial_id in self.trials:
            if self.trials[trial_id] != trial:
                raise ValueError("Trial is immutable")
            return self.model(action, condition, world)
        if trial_id in self.store.records:
            raise ValueError("Source ID already in use")
        raw = canonical({"action": action, "before": before, "treated_after": treated_after,
                         "control_after": control_after, "controlled": controlled,
                         "condition": condition, "world": world})
        self.store.add(trial_id, raw)
        self.trials[trial_id] = trial
        return self.model(action, condition, world)

    def model(self, action, condition="default", world="default"):
        trials = [t for t in self.trials.values() if (t.action, t.condition, t.world) == (action, condition, world)]
        controlled = [t for t in trials if t.controlled]
        base = {"action": action, "condition": condition, "world": world,
                "observations": len(trials), "controlled_trials": len(controlled),
                "support": tuple(t.trial_id for t in controlled),
                "scope": "paired_control_contrast_guard_v2"}
        if not trials:
            return {**base, "status": "NO_PATH"}
        if not controlled:
            return {**base, "status": "INCOMPLETE", "reason": "No controlled interventions"}
        if any(not self.store.alive(t.trial_id) for t in controlled):
            return {**base, "status": "INCOMPLETE", "reason": "Disconnected trial evidence"}
        if any(t.control != t.before for t in controlled):
            return {**base, "status": "CONFOUNDED", "reason": "Control path drifted from initial state"}
        keys = tuple(k for k, _ in controlled[0].before)
        if any(tuple(k for k, _ in t.before) != keys for t in controlled):
            return {**base, "status": "CONFLICT", "reason": "Measured sensor key-set changed"}
        positive = [t for t in controlled if t.before != t.treated]
        negative = [t for t in controlled if t.before == t.treated]
        if not positive:
            return {**base, "status": "NO_EFFECT", "reason": "No treatment/control difference observed"}
        models = set()
        for trial in positive:
            before, after = dict(trial.before), dict(trial.treated)
            changed = tuple(k for k in before if before[k] != after[k])
            local = tuple((k, before[k]) for k in changed)
            effect = tuple((k, after[k]) for k in changed)
            models.add((local, effect))
        if len(models) != 1:
            return {**base, "status": "CONFLICT", "reason": "Effects or local preconditions disagree"}
        _, effect = next(iter(models))
        before_states = [dict(t.before) for t in positive]
        guard = {k: before_states[0][k] for k in keys
                 if all(state[k] == before_states[0][k] for state in before_states)}
        contrast_witnesses = {}
        unsupported = []
        for key in keys:
            if key in guard:
                continue
            values = {state[key] for state in before_states}
            edges = []
            neighbors = {value: set() for value in values}
            for i, first in enumerate(before_states):
                for j in range(i+1, len(before_states)):
                    second = before_states[j]
                    if first[key] != second[key] and all(first[k] == second[k] for k in keys if k != key):
                        edges.append((positive[i].trial_id, positive[j].trial_id))
                        neighbors[first[key]].add(second[key])
                        neighbors[second[key]].add(first[key])
            reachable = set()
            todo = [min(values)]
            while todo:
                value = todo.pop()
                if value in reachable:
                    continue
                reachable.add(value)
                todo.extend(neighbors[value]-reachable)
            contrast_witnesses[key] = tuple(edges)
            if reachable != values:
                unsupported.append(key)
        effect = dict(effect)
        for trial in negative:
            before = dict(trial.before)
            if all(before[k] == v for k, v in guard.items()) and {**before, **effect} != before:
                return {**base, "status": "CONFLICT", "reason": "Guard admits an observed no-effect counterexample",
                        "counterexample": trial.trial_id}
        distinct = len({t.before for t in positive})
        details = {"distinct_states": distinct, "precondition": guard, "effect": effect,
                   "keys": keys, "contrast_witnesses": contrast_witnesses,
                   "negative_support": tuple(t.trial_id for t in negative)}
        if distinct < 3 or unsupported:
            return {**base, **details, "status": "INCOMPLETE", "unsupported_contrasts": unsupported,
                    "reason": "Insufficient independent positive contrasts"}
        return {**base, **details, "status": "SOLID"}

    def propose_trials(self, action, domains, condition="default", world="default", limit=16):
        for value in (action, condition, world):
            label(value)
        if not isinstance(domains, dict) or not domains or type(limit) is not int or limit < 1:
            raise ValueError("Declared domains and a positive proposal limit are required")
        keys = tuple(sorted(domains))
        values = []
        for key in keys:
            label(key)
            if not isinstance(domains[key], (tuple, list)) or not domains[key]:
                raise ValueError("Each sensor domain requires explicit values")
            values.append(tuple(sorted({label(v) for v in domains[key]})))
        trials = [t for t in self.trials.values() if (t.action,t.condition,t.world) == (action,condition,world) and t.controlled]
        if any(tuple(k for k, _ in t.before) != keys for t in trials):
            raise ValueError("Domain sensor keys differ from measured trials")
        for trial in trials:
            if any(v not in domains[k] for k, v in trial.before):
                raise ValueError("Declared domain excludes observed states")
        observed = {t.before for t in trials}
        successes = [t for t in trials if t.before != t.treated and t.before == t.control]
        proposals = []
        for vector in product(*values):
            state = tuple(zip(keys, vector))
            if state in observed:
                continue
            nearest = None
            changed = ()
            if successes:
                nearest = min(successes, key=lambda t:(sum(a != b for (_,a),(_,b) in zip(t.before,state)),t.trial_id))
                changed = tuple(k for (k,a),(_,b) in zip(nearest.before,state) if a != b)
            rank = (len(changed) if nearest else len(keys)+1, state)
            proposals.append((rank, {"action":action,"before":dict(state),"condition":condition,"world":world,
                                     "contrast_source":None if nearest is None else nearest.trial_id,
                                     "changed_ports":changed}))
        proposals.sort(key=lambda item:item[0])
        return {"proposals":[row for _,row in proposals[:limit]], "remaining_unobserved":len(proposals),
                "truncated":len(proposals)>limit, "domain_state_count":prod(len(v) for v in values)}

    def predict(self, action, before, condition="default", world="default"):
        state_tuple(before)
        model = self.model(action, condition, world)
        if model["status"] != "SOLID":
            return {"status": model["status"], "after": None, "model": model}
        if set(before) != set(model["keys"]) or any(before[k] != v for k, v in model["precondition"].items()):
            return {"status": "NO_PATH", "after": None, "model": model}
        return {"status": "RESOLVED", "after": {**before, **model["effect"]}, "model": model}

    def plan(self, before, goal, condition="default", world="default", max_depth=16, max_states=10000):
        start = state_tuple(before)
        state_tuple(goal)
        if not set(goal) <= set(before):
            raise ValueError("Goal refers to unmeasured sensors")
        if type(max_depth) is not int or max_depth < 0 or type(max_states) is not int or max_states < 1:
            raise ValueError("Invalid traversal budget")
        def met(state):
            return all(state[k] == value for k, value in goal.items())
        if met(before):
            return {"status": "RESOLVED", "after": dict(before), "steps": [], "visited": 1}
        actions = sorted({t.action for t in self.trials.values() if (t.condition, t.world) == (condition, world)})
        models = {a: self.model(a, condition, world) for a in actions}
        queue = deque([(start, ())])
        visited = {start}
        truncated = False
        while queue:
            current, steps = queue.popleft()
            state = dict(current)
            for action in actions:
                model = models[action]
                if model["status"] != "SOLID" or set(state) != set(model["keys"]):
                    continue
                if any(state[k] != v for k, v in model["precondition"].items()):
                    continue
                after = {**state, **model["effect"]}
                key = state_tuple(after)
                if key in visited:
                    continue
                if len(steps) >= max_depth or len(visited) >= max_states:
                    truncated = True
                    continue
                step = {"action": action, "before": state, "after": after, "support": model["support"]}
                path = steps+(step,)
                visited.add(key)
                if met(after):
                    return {"status": "RESOLVED", "after": after, "steps": list(path), "visited": len(visited)}
                queue.append((key, path))
        incomplete_evidence = any(m["status"] in ("INCOMPLETE", "CONFLICT", "CONFOUNDED") for m in models.values())
        return {"status": "INCOMPLETE" if truncated or incomplete_evidence else "NO_PATH",
                "after": None, "steps": [], "visited": len(visited),
                "reason": "Traversal budget or action evidence incomplete" if truncated or incomplete_evidence else "Reachable component exhausted"}

    def verify_plan(self, before, goal, result, condition="default", world="default"):
        state_tuple(before); state_tuple(goal)
        if result.get("status") != "RESOLVED":
            return False
        current = dict(before)
        for step in result.get("steps", []):
            if step.get("before") != current:
                return False
            prediction = self.predict(step.get("action"), current, condition, world)
            if prediction["status"] != "RESOLVED" or prediction["after"] != step.get("after") or prediction["model"]["support"] != step.get("support"):
                return False
            current = prediction["after"]
        return current == result.get("after") and all(current.get(k) == value for k, value in goal.items())

"""Set-valued raw-context transport from complete phase-valid organization."""
from .identity import encode, decode
from .organization import _match
from .organization_snapshot import snapshot
from .organization_inventory_check import verify_organization_inventory
from .role_work import RoleSearchBudget


def _query(domain, actions):
    if not isinstance(domain, (list, tuple)) or not domain:
        raise ValueError('Nonempty ordered context domain required')
    contexts = []
    for context in domain:
        if not isinstance(context, (list, tuple)) or not context:
            raise ValueError('Nonempty raw context frames required')
        frames = tuple(encode(f) for f in context)
        if any(not f for f in frames) or frames in contexts:
            raise ValueError('Empty frame or duplicate context')
        contexts.append(frames)
    if not isinstance(actions, (list, tuple)) or not actions:
        raise ValueError('Nonempty raw action inventory required')
    raw_actions = tuple(encode(a) for a in actions)
    if any(not a for a in raw_actions) or len(set(raw_actions)) != len(raw_actions):
        raise ValueError('Empty or duplicate action')
    return tuple(contexts), raw_actions


def certify_empirical_transport(model, domain, actions, *, max_search_steps=None):
    budget = RoleSearchBudget(max_search_steps)
    with budget.scope():
        contexts, raw_actions = _query(domain, actions)
        view = snapshot(model)
        if not verify_organization_inventory(view):
            raise ValueError('Incomplete or broken operator-experience inventory')
        rows = []
        for action in raw_actions:
            for index, context in enumerate(contexts):
                prefix = context + (action,)
                outcomes = {}; unbound = set(); revoked = []
                for anchor, h in sorted(view.organizations.items()):
                    budget.consume()
                    if len(prefix) >= len(h.pattern):
                        continue
                    for bindings, _ in _match(h.pattern, prefix):
                        if not view._phase_valid(h):
                            raise ValueError('Broken operator phase')
                        if set(bindings) != set(range(len(h.diversity))):
                            unbound.add(anchor); continue
                        output = tuple(tuple(i for k, v in parts for i in
                                             (v if k == 'lit' else bindings[v]))
                                       for parts in h.pattern[len(prefix):])
                        outcomes.setdefault(output, set()).add(anchor)
                for anchor, (h, _) in sorted(view.rejected_organizations.items()):
                    budget.consume()
                    if len(prefix) < len(h.pattern) and _match(h.pattern, prefix):
                        revoked.append(anchor)
                is_open = not outcomes or bool(unbound or revoked)
                outputs = [{'frames': list(map(decode, out)),
                            'witnesses': [{'anchor': a, 'sources': list(view.organizations[a].supports)}
                                          for a in sorted(anchors)]}
                           for out, anchors in sorted(outcomes.items())]
                edges = [j for j, destination in enumerate(contexts) if destination in outcomes]
                outside = [list(map(decode, out)) for out in sorted(outcomes) if out not in contexts]
                rows.append({'action': decode(action), 'from_context': index, 'outputs': outputs,
                             'supported_edges': edges, 'outside_domain': outside,
                             'unbound': sorted(unbound), 'revoked': revoked, 'open': is_open,
                             'possible_edges': list(range(len(contexts))) if is_open else edges,
                             'unknown_outside_domain': is_open})
        return {'policy': 'empirical_context_transport_v1',
                'domain': [list(map(decode, c)) for c in contexts],
                'actions': list(map(decode, raw_actions)),
                'sources': [{'source': s, 'frames': list(map(decode, frames))}
                            for s, (frames, _) in sorted(view.episodes.items())],
                'rows': rows}

"""Independent full-inventory checker; no transport producer or resolver calls."""
from .identity import encode, decode
from .organization import _match
from .organization_snapshot import snapshot
from .organization_inventory_check import verify_organization_inventory
from .frame_engine import canonical
from .role_work import RoleSearchBudget


def verify_empirical_transport(model, certificate, *, max_search_steps=None):
    budget = RoleSearchBudget(max_search_steps)
    with budget.scope():
        try:
            if set(certificate) != {'policy', 'domain', 'actions', 'sources', 'rows'}:
                return False
            if certificate['policy'] != 'empirical_context_transport_v1': return False
            domain = certificate['domain']; actions = certificate['actions']
            if not isinstance(domain, list) or not domain or not isinstance(actions, list) or not actions:
                return False
            raw_domain = []
            for context in domain:
                if not isinstance(context, list) or not context: return False
                item = tuple(encode(f) for f in context)
                if any(not f for f in item) or item in raw_domain: return False
                raw_domain.append(item)
            raw_actions = [encode(a) for a in actions]
            if any(not a for a in raw_actions) or len(set(raw_actions)) != len(raw_actions): return False
            view = snapshot(model)
            if not verify_organization_inventory(view): return False
            sources = [{'source': s, 'frames': [decode(f) for f in frames]}
                       for s, (frames, _) in sorted(view.episodes.items())]
            if canonical(sources) != canonical(certificate['sources']): return False
            expected = []
            for action in raw_actions:
                for origin in range(len(raw_domain)):
                    trigger = raw_domain[origin] + (action,)
                    supported = {}; partial = []; rejected = []
                    for anchor in sorted(view.organizations):
                        budget.consume(); org = view.organizations[anchor]
                        if len(org.pattern) <= len(trigger): continue
                        bindings = _match(org.pattern, trigger)
                        if bindings and not view._phase_valid(org): return False
                        incomplete = False
                        for assignment, _ in bindings:
                            if sorted(assignment) != list(range(len(org.diversity))):
                                incomplete = True; continue
                            result = []
                            for frame in org.pattern[len(trigger):]:
                                chars = []
                                for kind, value in frame:
                                    if kind == 'lit': chars.extend(value)
                                    else: chars.extend(assignment[value])
                                result.append(tuple(chars))
                            supported.setdefault(tuple(result), set()).add(anchor)
                        if incomplete: partial.append(anchor)
                    for anchor in sorted(view.rejected_organizations):
                        budget.consume(); org = view.rejected_organizations[anchor][0]
                        if len(org.pattern) > len(trigger) and _match(org.pattern, trigger): rejected.append(anchor)
                    outputs = []
                    for frames in sorted(supported):
                        witnesses = []
                        for anchor in sorted(supported[frames]):
                            witnesses.append({'anchor': anchor, 'sources': list(view.organizations[anchor].supports)})
                        outputs.append({'frames': [decode(f) for f in frames], 'witnesses': witnesses})
                    edges = []; outside = []
                    for frames in sorted(supported):
                        if frames in raw_domain: edges.append(raw_domain.index(frames))
                        else: outside.append([decode(f) for f in frames])
                    edges.sort()
                    open_row = len(outputs) == 0 or len(partial) > 0 or len(rejected) > 0
                    expected.append({'action': decode(action), 'from_context': origin, 'outputs': outputs,
                                     'supported_edges': edges, 'outside_domain': outside,
                                     'unbound': partial, 'revoked': rejected, 'open': open_row,
                                     'possible_edges': list(range(len(raw_domain))) if open_row else edges,
                                     'unknown_outside_domain': open_row})
            return canonical(expected) == canonical(certificate['rows'])
        except (ValueError, TypeError, KeyError, IndexError, AttributeError):
            return False

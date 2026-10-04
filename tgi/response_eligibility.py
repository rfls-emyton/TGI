"""Evidence-bound empirical eligibility of set-valued terminal response relations."""
from .identity import decode
from .organization import _match,OMEGA_CRIT
from .organization_inventory_check import verify_organization_inventory
from .organization_snapshot import snapshot


def certify_response_eligibility(model):
    parent=role=snapshot(model)
    if not verify_organization_inventory(parent):
        raise ValueError('Incomplete or stale organization inventory')
    grouped = {}
    for source, (frames, _) in sorted(role.episodes.items()):
        if len(frames)>=2:grouped.setdefault(frames[:-1], []).append((source, frames[-1]))
    groups = [{'input':[decode(f) for f in prefix],
               'outputs':[decode(f) for f in sorted({value for _,value in members})],
               'sources':[s for s,_ in members]} for prefix,members in sorted(grouped.items())]
    entries = dict(role.organizations)
    entries.update({a:h for a,(h,_) in role.rejected_organizations.items()})
    rows = []
    for anchor,h in sorted(entries.items()):
        checks=[];support_values=[set() for _ in h.diversity];opposed=False
        for prefix,members in sorted(grouped.items()):
            values=set();unbound=False
            matches=[]
            if len(h.pattern)==len(prefix)+1:
                matches=_match(h.pattern,prefix)
                for bindings,_ in matches:
                    if any(k=='axis' and v not in bindings for k,v in h.pattern[-1]):
                        unbound=True;continue
                    values.add(tuple(x for k,v in h.pattern[-1] for x in (v if k=='lit' else bindings[v])))
            actual={value for _,value in members}
            state='absent' if not matches else 'ambiguous' if len(matches)>1 else 'unbound'
            if len(matches)==1 and set(matches[0][0])==set(range(len(support_values))):
                if values-actual:state='opposed';opposed=True
                else:
                    state='supported'
                    for axis,value in matches[0][0].items():support_values[axis].add(value)
            checks.append({'predictions':[decode(x) for x in sorted(values)],'unbound':unbound,
                           'outside_observed':[decode(x) for x in sorted(values-actual)],
                           'match_count':len(matches),'binding_state':state})
        rows.append({'anchor':anchor,'original_phase':'active' if anchor in role.organizations else 'rejected',
                     'checks':checks,'identifiable_values':[[decode(v) for v in sorted(a)] for a in support_values],
                     'eligible':not opposed and all(len(v)>=OMEGA_CRIT for v in support_values)})
    return {'policy':'input_identifiable_v1','sources':[{'source':s,'frames':[decode(f) for f in frames]} for s,(frames,_) in sorted(parent.episodes.items())],
            'groups':groups,'organizations':rows}

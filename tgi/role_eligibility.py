"""Evidence-bound empirical eligibility of set-valued raw query relations."""
from .identity import decode
from .organization import _match
from .role_projection_check import verify_role_projection


def certify_role_eligibility(parent, role):
    if not verify_role_projection(parent, role):
        raise ValueError('Incomplete or stale role projection')
    grouped = {}
    for source, (frames, _) in sorted(role.episodes.items()):
        grouped.setdefault(frames[:-1], []).append((source, frames[-1]))
    groups = [{'input':[decode(f) for f in prefix],
               'outputs':[decode(f) for f in sorted({value for _,value in members})],
               'sources':[s for s,_ in members]} for prefix,members in sorted(grouped.items())]
    entries = dict(role.organizations)
    entries.update({a:h for a,(h,_) in role.rejected_organizations.items()})
    rows = []
    for anchor,h in sorted(entries.items()):
        checks=[]
        for prefix,members in sorted(grouped.items()):
            values=set();unbound=False
            if len(h.pattern)==len(prefix)+1:
                for bindings,_ in _match(h.pattern,prefix):
                    if any(k=='axis' and v not in bindings for k,v in h.pattern[-1]):
                        unbound=True;continue
                    values.add(tuple(x for k,v in h.pattern[-1] for x in (v if k=='lit' else bindings[v])))
            actual={value for _,value in members}
            checks.append({'predictions':[decode(x) for x in sorted(values)],'unbound':unbound,
                           'outside_observed':[decode(x) for x in sorted(values-actual)]})
        rows.append({'anchor':anchor,'original_phase':'active' if anchor in role.organizations else 'rejected',
                     'checks':checks,'eligible':all(not c['unbound'] and not c['outside_observed'] for c in checks)})
    return {'sources':[{'source':s,'frames':[decode(f) for f in frames]} for s,(frames,_) in sorted(parent.episodes.items())],
            'groups':groups,'organizations':rows}

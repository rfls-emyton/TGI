"""Recompute relational eligibility without producer or resolver calls."""
from .identity import decode
from .frame_engine import canonical
from .organization import _match
from .role_projection_check import verify_role_projection


def verify_role_eligibility(parent, role, certificate):
    try:
        if not verify_role_projection(parent,role):return False
        # Derive grouping directly from original complete episodes.
        prefixes=sorted({frames[:-2] for frames,_ in parent.episodes.values() if len(frames)>=3})
        groups=[];raw_groups=[]
        for prefix in prefixes:
            sources=[];outputs=set()
            for source,(frames,_) in sorted(parent.episodes.items()):
                if len(frames)>=3 and frames[:-2]==prefix:
                    sources.append(source);outputs.add(frames[-2])
            groups.append({'input':list(map(decode,prefix)),'outputs':list(map(decode,sorted(outputs))),'sources':sources})
            raw_groups.append((prefix,outputs))
        organizations=[]
        for anchor in sorted(set(role.organizations)|set(role.rejected_organizations)):
            active=anchor in role.organizations
            h=role.organizations[anchor] if active else role.rejected_organizations[anchor][0]
            checks=[];eligible=True
            for prefix,observed in raw_groups:
                predictions=set();unbound=False
                if len(prefix)+1==len(h.pattern):
                    for bindings,_ in _match(h.pattern,prefix):
                        result=[];complete=True
                        for kind,value in h.pattern[-1]:
                            if kind=='lit':result.extend(value)
                            elif value in bindings:result.extend(bindings[value])
                            else:complete=False
                        if complete:predictions.add(tuple(result))
                        else:unbound=True
                outside=sorted(v for v in predictions if v not in observed)
                eligible=eligible and not unbound and not outside
                checks.append({'predictions':list(map(decode,sorted(predictions))),'unbound':unbound,
                               'outside_observed':list(map(decode,outside))})
            organizations.append({'anchor':anchor,'original_phase':'active' if active else 'rejected',
                                  'checks':checks,'eligible':bool(eligible)})
        expected={'sources':[{'source':s,'frames':list(map(decode,frames))} for s,(frames,_) in sorted(parent.episodes.items())],
                  'groups':groups,'organizations':organizations}
        return canonical(certificate)==canonical(expected)
    except (TypeError,ValueError,KeyError,IndexError,AttributeError):return False

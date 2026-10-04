"""Recompute relational eligibility without producer or resolver calls."""
from .identity import decode
from .frame_engine import canonical
from .organization import _match,OMEGA_CRIT
from .organization_inventory_check import verify_organization_inventory
from .organization_snapshot import snapshot


def verify_response_eligibility(model, certificate):
    try:
        parent=role=snapshot(model)
        if not verify_organization_inventory(parent):return False
        # Derive grouping directly from original complete episodes.
        prefixes=sorted({frames[:-1] for frames,_ in parent.episodes.values() if len(frames)>=2})
        groups=[];raw_groups=[]
        for prefix in prefixes:
            sources=[];outputs=set()
            for source,(frames,_) in sorted(parent.episodes.items()):
                if len(frames)>=2 and frames[:-1]==prefix:
                    sources.append(source);outputs.add(frames[-1])
            groups.append({'input':list(map(decode,prefix)),'outputs':list(map(decode,sorted(outputs))),'sources':sources})
            raw_groups.append((prefix,outputs))
        organizations=[]
        for anchor in sorted(set(role.organizations)|set(role.rejected_organizations)):
            active=anchor in role.organizations
            h=role.organizations[anchor] if active else role.rejected_organizations[anchor][0]
            checks=[];eligible=True;distinct=[set() for _ in h.diversity]
            for prefix,observed in raw_groups:
                predictions=set();unbound=False;matches=[]
                if len(prefix)+1==len(h.pattern):
                    matches=_match(h.pattern,prefix)
                    for bindings,_ in matches:
                        result=[];complete=True
                        for kind,value in h.pattern[-1]:
                            if kind=='lit':result.extend(value)
                            elif value in bindings:result.extend(bindings[value])
                            else:complete=False
                        if complete:predictions.add(tuple(result))
                        else:unbound=True
                outside=sorted(v for v in predictions if v not in observed)
                state='absent' if len(matches)==0 else 'ambiguous' if len(matches)>1 else 'unbound'
                if len(matches)==1 and sorted(matches[0][0])==list(range(len(distinct))):
                    if outside:state='opposed';eligible=False
                    else:
                        state='supported'
                        for axis in range(len(distinct)):distinct[axis].add(matches[0][0][axis])
                checks.append({'predictions':list(map(decode,sorted(predictions))),'unbound':unbound,
                               'outside_observed':list(map(decode,outside)),'match_count':len(matches),'binding_state':state})
            organizations.append({'anchor':anchor,'original_phase':'active' if active else 'rejected',
                                  'checks':checks,'identifiable_values':[list(map(decode,sorted(v))) for v in distinct],
                                  'eligible':bool(eligible and all(len(v)>=OMEGA_CRIT for v in distinct))})
        expected={'policy':'input_identifiable_v1','sources':[{'source':s,'frames':list(map(decode,frames))} for s,(frames,_) in sorted(parent.episodes.items())],
                  'groups':groups,'organizations':organizations}
        return canonical(certificate)==canonical(expected)
    except (TypeError,ValueError,KeyError,IndexError,AttributeError):return False

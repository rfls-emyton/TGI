"""Independent complete binding and output reconstruction for role readout."""
from .identity import encode,decode
from .organization import _match
from .frame_engine import canonical
from .role_eligibility_check import verify_role_eligibility
from .organization_snapshot import snapshot


def verify_role_readout(parent,role,certificate):
    try:
        parent=snapshot(parent);role=snapshot(role)
        if not verify_role_eligibility(parent,role,certificate['eligibility']):return False
        return _verify_role_readout_contents(parent,role,certificate)
    except (TypeError,ValueError,KeyError,IndexError,AttributeError):return False


def _verify_role_readout_contents(parent,role,certificate):
    """Internal: caller holds immutable snapshots and verified shared eligibility."""
    try:
        eligibility=certificate['eligibility'];prefix=certificate['prefix']
        if not isinstance(prefix,list) or not prefix or any(not isinstance(f,str) or not f for f in prefix):return False
        raw=tuple(map(encode,prefix))
        rows=[];eligible_values=set();excluded_values=set();unbound_anchors=[]
        for decision in eligibility['organizations']:
            anchor=decision['anchor']
            h=role.organizations[anchor] if anchor in role.organizations else role.rejected_organizations[anchor][0]
            matches=[];outputs=set();unbound=False
            if len(h.pattern)==len(raw)+1:
                for bindings,locations in _match(h.pattern,raw):
                    output=[];missing=False
                    for kind,value in h.pattern[-1]:
                        if kind=='lit':output.extend(value)
                        elif value in bindings:output.extend(bindings[value])
                        else:missing=True
                    text=None if missing else decode(output)
                    if missing:unbound=True
                    else:outputs.add(text)
                    matches.append({'bindings':[[axis,list(bindings[axis])] for axis in sorted(bindings)],
                                    'locations':[[point[0],point[1],*locations[point]] for point in sorted(locations)],'output':text})
            rows.append({'anchor':anchor,'eligible':decision['eligible'],'matches':matches,'outputs':sorted(outputs),'unbound':unbound})
            if unbound:unbound_anchors.append(anchor)
            if decision['eligible']:eligible_values.update(outputs)
            else:excluded_values.update(outputs)
        observed=set()
        for frames,_ in parent.episodes.values():
            if len(frames)>=3 and frames[:-2]==raw:observed.add(decode(frames[-2]))
        expected={'eligibility':eligibility,'prefix':prefix,'organizations':rows,
                  'result':{'observed_outputs':sorted(observed),'eligible_outputs':sorted(eligible_values),
                            'excluded_outputs':sorted(excluded_values),'unbound_anchors':unbound_anchors}}
        return canonical(certificate)==canonical(expected)
    except (TypeError,ValueError,KeyError,IndexError,AttributeError):return False

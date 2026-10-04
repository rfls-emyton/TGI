"""Complete relational candidate readout; never selects a semantic truth."""
from .identity import encode,decode
from .organization import _match
from .role_eligibility_check import verify_role_eligibility


def certify_role_readout(parent,role,eligibility,prefix):
    if not isinstance(prefix,(list,tuple)) or not prefix or any(not isinstance(f,str) or not f for f in prefix):
        raise ValueError('Nonempty raw frame sequence required')
    raw=tuple(encode(f) for f in prefix)
    if not verify_role_eligibility(parent,role,eligibility):raise ValueError('Invalid relational evidence')
    entries=dict(role.organizations);entries.update({a:h for a,(h,_) in role.rejected_organizations.items()})
    rows=[];included=set();excluded=set();unresolved=[]
    for admission in eligibility['organizations']:
        anchor=admission['anchor'];h=entries[anchor];values=set();matches=[];unbound=False
        if len(h.pattern)==len(raw)+1:
            for bindings,locations in _match(h.pattern,raw):
                complete=all(k=='lit' or v in bindings for k,v in h.pattern[-1])
                output=decode(tuple(x for k,v in h.pattern[-1] for x in (v if k=='lit' else bindings[v]))) if complete else None
                if output is not None:values.add(output)
                else:unbound=True
                matches.append({'bindings':[[a,list(v)] for a,v in sorted(bindings.items())],
                                'locations':[[f,p,start,stop] for (f,p),(start,stop) in sorted(locations.items())],
                                'output':output})
        rows.append({'anchor':anchor,'eligible':admission['eligible'],'matches':matches,'outputs':sorted(values),'unbound':unbound})
        (included if admission['eligible'] else excluded).update(values)
        if unbound:unresolved.append(anchor)
    observed=sorted({decode(frames[-1]) for frames,_ in role.episodes.values() if frames[:-1]==raw})
    return {'eligibility':eligibility,'prefix':list(prefix),'organizations':rows,
            'result':{'observed_outputs':observed,'eligible_outputs':sorted(included),
                      'excluded_outputs':sorted(excluded),'unbound_anchors':unresolved}}

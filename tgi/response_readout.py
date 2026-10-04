"""All empirical response alternatives with original character provenance."""
from .identity import encode,decode
from .organization import _match
from .organization_snapshot import snapshot
from .response_eligibility_check import verify_response_eligibility
from .observed_response import certify_observed_response


def certify_response_readout(model,eligibility,prefix):
    if not isinstance(prefix,(list,tuple)) or not prefix or any(not isinstance(x,str) or not x for x in prefix):raise ValueError('Raw prefix required')
    model=snapshot(model);raw=tuple(map(encode,prefix))
    if not verify_response_eligibility(model,eligibility):raise ValueError('Invalid response eligibility')
    rows=[];included=set();unbound=[]
    for decision in eligibility['organizations']:
        anchor=decision['anchor'];h=model.organizations.get(anchor)
        if h is None:h=model.rejected_organizations[anchor][0]
        matches=[]
        if len(h.pattern)==len(raw)+1:
            for binding,locations in _match(h.pattern,raw):
                missing=any(k=='axis' and v not in binding for k,v in h.pattern[-1])
                text=None;trace=None
                if not missing:
                    source=h.supports[0];frames,receipts=model.episodes[source]
                    source_binding=_match(h.pattern,frames)[0][0]
                    ids=[];trace=[];offset=0;fi=len(raw)
                    for kind,value in h.pattern[-1]:
                        if kind=='lit':
                            origin=receipts[fi].origin
                            for j,identity in enumerate(value):
                                ids.append(identity);trace.append({'kind':'crystal','source':source,'frame':fi,
                                    'position':offset+j,'coordinate':list((origin[0]+offset+j,)+origin[1:])})
                            offset+=len(value)
                        else:
                            point=next(p for p in sorted(locations) if h.pattern[p[0]][p[1]]==('axis',value))
                            start,stop=locations[point]
                            ids.extend(raw[point[0]][start:stop])
                            trace.extend({'kind':'trigger','frame':point[0],'position':j} for j in range(start,stop))
                            offset+=len(source_binding[value])
                    text=decode(ids)
                matches.append({'bindings':[[a,list(v)] for a,v in sorted(binding.items())],
                                'locations':[[f,p,a,b] for (f,p),(a,b) in sorted(locations.items())],
                                'output':text,'characters':trace})
        identifiable=len(matches)==1 and len(matches[0]['bindings'])==len(h.diversity)
        if decision['eligible'] and identifiable and matches[0]['output'] is not None:included.add(matches[0]['output'])
        if decision['eligible'] and len(matches)==1 and not identifiable:unbound.append(anchor)
        rows.append({'anchor':anchor,'eligible':decision['eligible'],'input_identifiable':identifiable,'matches':matches})
    observed=certify_observed_response(model,list(prefix));actual=observed['result']
    if actual['status']=='OBSERVED_CONFLICT':status='UNRESOLVED';output=[];basis='observed_conflict'
    elif actual['status']=='OBSERVED_AGREEMENT':status='OBSERVED_RESPONSE';output=actual['output'];basis='observed'
    elif len(included)==1 and not unbound:status='CONDITIONAL_RESPONSE';output=sorted(included);basis='empirical_relation'
    else:status='UNRESOLVED';output=[];basis='empirical_relation'
    return {'eligibility':eligibility,'prefix':list(prefix),'organizations':rows,'observed':observed,
            'result':{'status':status,'basis':basis,'output':output,'alternatives':sorted(included),'unbound_anchors':sorted(set(unbound))}}

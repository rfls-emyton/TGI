"""Independent full binding, character and response-policy reconstruction."""
from .identity import encode,decode
from .frame_engine import canonical
from .organization import _match
from .organization_snapshot import snapshot
from .response_eligibility_check import verify_response_eligibility
from .observed_response_check import verify_observed_response


def _verify_response_readout_contents(model,certificate):
    """Internal: caller has verified this relation on this immutable snapshot."""
    try:
        eligibility=certificate['eligibility'];prefix=certificate['prefix']
        if not isinstance(prefix,list) or not prefix or any(not isinstance(f,str) or not f for f in prefix):return False
        raw=tuple(map(encode,prefix))
        observed=certificate['observed']
        if observed['prefix']!=prefix or not verify_observed_response(model,observed):return False
        rows=[];outputs=set();unbound=set()
        for decision in eligibility['organizations']:
            anchor=decision['anchor']
            h=model.organizations[anchor] if anchor in model.organizations else model.rejected_organizations[anchor][0]
            records=[]
            if len(h.pattern)==len(raw)+1:
                for bindings,locations in _match(h.pattern,raw):
                    complete=all(kind=='lit' or value in bindings for kind,value in h.pattern[-1])
                    output=None;characters=None
                    if complete:
                        ids=[];characters=[];source=h.supports[0];frames,receipts=model.episodes[source]
                        support_bindings=_match(h.pattern,frames)[0][0];position=0;fi=len(raw)
                        for kind,value in h.pattern[-1]:
                            if kind=='lit':
                                for identity in value:
                                    if frames[fi][position]!=identity:return False
                                    origin=receipts[fi].origin
                                    coordinate=[origin[0]+position,*origin[1:]]
                                    if model.frames.view().atoms[tuple(coordinate)].identity!=identity:return False
                                    ids.append(identity);characters.append({'kind':'crystal','source':source,'frame':fi,'position':position,'coordinate':coordinate})
                                    position+=1
                            else:
                                positions=sorted(p for p in locations if h.pattern[p[0]][p[1]]==('axis',value))
                                point=positions[0];a,b=locations[point]
                                if raw[point[0]][a:b]!=bindings[value]:return False
                                for i in range(a,b):
                                    ids.append(raw[point[0]][i]);characters.append({'kind':'trigger','frame':point[0],'position':i})
                                position+=len(support_bindings[value])
                        output=decode(ids)
                    records.append({'bindings':[[a,list(bindings[a])] for a in sorted(bindings)],
                                    'locations':[[p[0],p[1],*locations[p]] for p in sorted(locations)],
                                    'output':output,'characters':characters})
            identifiable=len(records)==1 and len(records[0]['bindings'])==len(h.diversity)
            if decision['eligible'] and identifiable and records[0]['output'] is not None:outputs.add(records[0]['output'])
            if decision['eligible'] and len(records)==1 and not identifiable:unbound.add(anchor)
            rows.append({'anchor':anchor,'eligible':decision['eligible'],'input_identifiable':identifiable,'matches':records})
        actual=observed['result']
        if actual['status']=='OBSERVED_CONFLICT':
            result={'status':'UNRESOLVED','basis':'observed_conflict','output':[]}
        elif actual['status']=='OBSERVED_AGREEMENT':
            result={'status':'OBSERVED_RESPONSE','basis':'observed','output':actual['output']}
        elif len(outputs)==1 and not unbound:
            result={'status':'CONDITIONAL_RESPONSE','basis':'empirical_relation','output':sorted(outputs)}
        else:result={'status':'UNRESOLVED','basis':'empirical_relation','output':[]}
        result.update(alternatives=sorted(outputs),unbound_anchors=sorted(unbound))
        expected={'eligibility':eligibility,'prefix':prefix,'organizations':rows,'observed':observed,'result':result}
        return canonical(expected)==canonical(certificate)
    except (KeyError,TypeError,ValueError,IndexError,AttributeError,StopIteration):return False


def verify_response_readout(model,certificate):
    try:
        model=snapshot(model)
        if not verify_response_eligibility(model,certificate['eligibility']):return False
        return _verify_response_readout_contents(model,certificate)
    except (KeyError,TypeError,ValueError,IndexError,AttributeError,StopIteration):return False

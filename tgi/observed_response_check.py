"""Independent scope, occurrence and observed-response consensus verification."""
from .identity import encode,decode
from .frame_engine import canonical
from .organization_snapshot import snapshot


def verify_observed_response(model,certificate):
    try:
        prefix=certificate['prefix']
        if not isinstance(prefix,list) or not prefix or any(not isinstance(f,str) or not f for f in prefix):return False
        raw=tuple(map(encode,prefix));view=snapshot(model);rows=[];values=set()
        for source in sorted(view.episodes):
            if not view._alive(source):return False
            frames,receipts=view.episodes[source]
            if len(frames)!=len(raw)+1 or any(frames[i]!=raw[i] for i in range(len(raw))):continue
            endpoints=[];offset=0
            for i,frame in enumerate(frames):
                origin=receipts[i].origin
                endpoints.append({'frame':i,'start':0,'stop':len(frame),'event_span':[offset,offset+len(frame)],
                                  'identities':list(frame),'coordinates':[list((origin[0]+j,)+origin[1:]) for j in range(len(frame))]})
                offset+=len(frame)
            text=decode(frames[-1]);values.add(text);rows.append({'source':source,'output':text,'occurrences':endpoints})
        status={0:'NO_OBSERVATION',1:'OBSERVED_AGREEMENT'}.get(len(values),'OBSERVED_CONFLICT')
        expected={'prefix':prefix,'scope':sorted(view.episodes),'observations':rows,
                  'result':{'status':status,'output':sorted(values) if len(values)==1 else [],'candidates':sorted(values)}}
        return canonical(certificate)==canonical(expected)
    except (TypeError,ValueError,KeyError,IndexError,AttributeError):return False

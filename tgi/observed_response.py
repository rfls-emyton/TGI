"""Complete direct crystal observations, separate from inferred rule eligibility."""
from .identity import encode,decode
from .organization_snapshot import snapshot
from .incidence import _endpoint


def certify_observed_response(model,prefix):
    if not isinstance(prefix,(list,tuple)) or not prefix or any(not isinstance(f,str) or not f for f in prefix):
        raise ValueError('Nonempty raw prefix required')
    raw=tuple(map(encode,prefix));view=snapshot(model)
    if not all(view._alive(s) for s in view.episodes):raise ValueError('Broken source evidence')
    rows=[];outputs=set()
    for source,(frames,_) in sorted(view.episodes.items()):
        if len(frames)!=len(raw)+1 or frames[:-1]!=raw:continue
        output=decode(frames[-1]);outputs.add(output)
        rows.append({'source':source,'output':output,
                     'occurrences':[_endpoint(view,source,(i,0,len(frame))) for i,frame in enumerate(frames)]})
    status='OBSERVED_CONFLICT' if len(outputs)>1 else 'OBSERVED_AGREEMENT' if outputs else 'NO_OBSERVATION'
    return {'prefix':list(prefix),'scope':sorted(view.episodes),'observations':rows,
            'result':{'status':status,'output':[next(iter(outputs))] if len(outputs)==1 else [],'candidates':sorted(outputs)}}

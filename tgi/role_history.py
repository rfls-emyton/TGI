"""Source-local temporal frontier preserving distinct role evidence classes."""
from .identity import decode
from .incidence import _endpoint
from .observation_point import _validate
from .organization_snapshot import snapshot
from .role_eligibility_check import verify_role_eligibility
from .role_readout import certify_role_readout


def certify_role_history(model,role,eligibility,history,source,stop,query):
    _validate(history,source,stop,query)
    if not verify_role_eligibility(model,role,eligibility):raise ValueError('Invalid role evidence')
    view=snapshot(history)
    if not view._alive(source):raise ValueError('Broken history')
    frames=view.episodes[source][0]
    lengths=sorted({len(f)-1 for f,_ in role.episodes.values()})
    windows=[];readouts=[];cache={}
    for end in range(1,stop+1):
        for size in lengths:
            if size>end:continue
            start=end-size;prefix=tuple(decode(f) for f in frames[start:end])
            if prefix not in cache:
                cache[prefix]=len(readouts)
                readouts.append(certify_role_readout(model,role,eligibility,list(prefix)))
            windows.append({'start':start,'stop':end,'readout':cache[prefix],
                            'occurrences':[_endpoint(view,source,(i,0,len(frames[i]))) for i in range(start,end)]})
    frontier={}
    for kind in ('observed','eligible','excluded','unbound'):
        indexes=[]
        for i,w in enumerate(windows):
            r=readouts[w['readout']]['result']
            matches=bool(r['unbound_anchors']) if kind=='unbound' else query in r[kind+'_outputs']
            if matches:indexes.append(i)
        latest=max((windows[i]['stop'] for i in indexes),default=None)
        frontier[kind]=[i for i in indexes if windows[i]['stop']==latest]
    return {'eligibility':eligibility,'point':{'source':source,'stop':stop,'event_offset':sum(map(len,frames[:stop]))},
            'query':query,'readouts':readouts,'windows':windows,'frontier':frontier}

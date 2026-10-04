"""Bind conditional feedback to actual source-local NMU occurrences."""
from .identity import decode
from .organization_snapshot import snapshot
from .frame_engine import canonical
from .incidence import _endpoint
from .separation import refine_separation
from .separation_check import verify_refinement


def refine_observed(engine,plan,source,request_frame,response_stop,*,acquisition=None):
    if not isinstance(source,str) or not source:raise ValueError('Source required')
    if any(type(x) is not int for x in (request_frame,response_stop)):raise ValueError('Integer frame boundaries required')
    view=snapshot(engine if acquisition is None else acquisition)
    if source not in view.episodes:raise KeyError(source)
    frames=view.episodes[source][0]
    if not 0<=request_frame<response_stop-1<len(frames):raise ValueError('Request followed by nonempty response interval required')
    if not view._alive(source):raise ValueError('Broken acquisition evidence')
    request=decode(frames[request_frame]);observed=[decode(f) for f in frames[request_frame+1:response_stop]]
    refinement=refine_separation(engine,plan,request,observed)
    return {'source':source,'request_frame':request_frame,'response_stop':response_stop,
            'occurrences':[_endpoint(view,source,(i,0,len(frames[i]))) for i in range(request_frame,response_stop)],
            'refinement':refinement}


def verify_observed_refinement(engine,certificate,*,acquisition=None):
    try:
        if set(certificate)!={'source','request_frame','response_stop','occurrences','refinement'}:return False
        if engine._dirty:return False
        view=snapshot(engine if acquisition is None else acquisition);source=certificate['source']
        first=certificate['request_frame'];stop=certificate['response_stop']
        if not isinstance(source,str) or not source or any(type(v) is not int for v in (first,stop)):return False
        frames,receipts=view.episodes[source]
        if not 0<=first<stop-1<len(frames) or not view._alive(source):return False
        expected=[]
        for i in range(first,stop):
            offset=sum(len(f) for f in frames[:i]);size=len(frames[i]);origin=receipts[i].origin
            expected.append({'frame':i,'start':0,'stop':size,'event_span':[offset,offset+size],
                             'identities':list(frames[i]),'coordinates':[[origin[0]+j,*origin[1:]] for j in range(size)]})
        if canonical(expected)!=canonical(certificate['occurrences']):return False
        r=certificate['refinement']
        if r['request']!=decode(frames[first]) or r['observed']!=[decode(f) for f in frames[first+1:stop]]:return False
        return verify_refinement(engine,r)
    except (KeyError,IndexError,TypeError,ValueError,AttributeError):return False

"""Independent source-local actual-feedback verification."""
from .identity import encode,decode
from .frame_engine import canonical
from .organization_snapshot import snapshot
from .role_proposal_check import verify_role_proposal


def verify_role_feedback(model,role,acquisition,certificate):
    try:
        history=snapshot(acquisition);proposal=certificate['proposal']
        if not verify_role_proposal(model,role,history,proposal):return False
        source=proposal['context']['source'];fi=proposal['context']['stop']
        frames,receipts=history.episodes[source]
        if fi+1>=len(frames) or frames[fi]!=encode(proposal['candidates']['query']):return False
        occurrences=[]
        for i in (fi,fi+1):
            origin=receipts[i].origin;offset=sum(map(len,frames[:i]));size=len(frames[i])
            occurrences.append({'frame':i,'start':0,'stop':size,'event_span':[offset,offset+size],
                'identities':list(frames[i]),'coordinates':[[origin[0]+j,*origin[1:]] for j in range(size)]})
        expected={'proposal':proposal,'feedback':{'source':source,'request_frame':fi,'response_frame':fi+1,
                  'response':decode(frames[fi+1]),'occurrences':occurrences}}
        return canonical(expected)==canonical(certificate)
    except (KeyError,ValueError,TypeError,IndexError,AttributeError):return False

"""Bind feedback to the same source-local context as a verified proposal."""
from .identity import decode,encode
from .organization_snapshot import snapshot
from .incidence import _endpoint
from .role_proposal_check import verify_role_proposal


def certify_role_feedback(model,role,acquisition,proposal):
    history=snapshot(acquisition)
    if not verify_role_proposal(model,role,history,proposal):raise ValueError('Invalid proposal')
    context=proposal['context'];source=context['source'];fi=context['stop']
    frames=history.episodes[source][0]
    if fi+1>=len(frames) or frames[fi]!=encode(proposal['candidates']['query']):raise ValueError('Matching request and actual response required')
    return {'proposal':proposal,'feedback':{'source':source,'request_frame':fi,'response_frame':fi+1,
            'response':decode(frames[fi+1]),'occurrences':[_endpoint(history,source,(i,0,len(frames[i]))) for i in (fi,fi+1)]}}

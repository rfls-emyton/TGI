"""Check raw episode delta, retained occurrences and candidate/response evidence."""
from .role_feedback_check import verify_role_feedback
from .role_candidates_check import verify_role_candidates
from .observed_response_check import verify_observed_response
from .organization_snapshot import snapshot


def verify_feedback_update(before,role,acquisition,after,after_role,certificate):
    try:
        if set(certificate)!={'feedback','source','after_candidates','observed_before','observed_after'}:return False
        before=snapshot(before);after=snapshot(after);acquisition=snapshot(acquisition)
        feedback=certificate['feedback'];source=certificate['source']
        if not isinstance(source,str) or not source.strip() or source in before.episodes:return False
        if not verify_role_feedback(before,role,acquisition,feedback):return False
        proposal=feedback['proposal'];context=proposal['context']
        raw=acquisition.episodes[context['source']][0][context['start']:feedback['feedback']['response_frame']+1]
        if set(after.episodes)!=set(before.episodes)|{source}:return False
        if after.episodes[source][0]!=raw or not after._alive(source):return False
        if any(after.episodes[s]!=value for s,value in before.episodes.items()):return False
        old=before.frames.view();new=after.frames.view()
        for attr in ('atoms','bonds','origins'):
            a=getattr(old,attr);b=getattr(new,attr)
            if any(b.get(k)!=v for k,v in a.items()):return False
        coords=set();anchors=set()
        for frame,receipt in zip(*after.episodes[source]):
            anchors.add(receipt.anchor)
            coords.update((receipt.origin[0]+p,)+receipt.origin[1:] for p in range(len(frame)))
        if set(new.atoms)!=set(old.atoms)|coords or set(new.origins)!=set(old.origins)|anchors:return False
        if not set(new.bonds)<=set(old.bonds)|coords:return False
        candidate=certificate['after_candidates'];previous=proposal['candidates']
        if candidate['prefix']!=previous['prefix'] or candidate['query']!=previous['query']:return False
        if not verify_role_candidates(after,after_role,candidate):return False
        prefix=previous['prefix']+[previous['query']]
        for engine,key in ((before,'observed_before'),(after,'observed_after')):
            observed=certificate[key]
            if observed['prefix']!=prefix or not verify_observed_response(engine,observed):return False
        return True
    except (KeyError,ValueError,TypeError,IndexError,AttributeError):return False

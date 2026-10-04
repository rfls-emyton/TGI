"""Independent complete-epoch and latest observation frontier verification."""
from .identity import decode
from .organization_snapshot import snapshot
from .separation_check import verify_separating_requests
from .frame_engine import canonical


def verify_observation_epochs(model, acquisition, certificate):
    try:
        if set(certificate) != {'policy','source','boundaries','epochs','result'}:
            return False
        if certificate['policy'] != 'independent_observation_epochs_v1':
            return False
        model = snapshot(model)
        history = snapshot(acquisition)
        source = certificate['source']
        if not isinstance(source, str) or not source or not history._alive(source):
            return False
        frames, receipts = history.episodes[source]
        bounds = certificate['boundaries']
        if (not isinstance(bounds, list) or len(bounds) < 2
                or any(type(x) is not int for x in bounds)
                or bounds[0] != 0 or bounds[-1] != len(frames)
                or any(b-a < 2 for a,b in zip(bounds,bounds[1:]))):
            return False
        epochs = certificate['epochs']
        if not isinstance(epochs,list) or len(epochs) != len(bounds)-1:
            return False
        for n, row in enumerate(epochs):
            if set(row) != {'plan','occurrences'}:
                return False
            start,stop = bounds[n:n+2]
            plan = row['plan']
            if (plan['request'] != decode(frames[start])
                    or plan['observed'] != [decode(f) for f in frames[start+1:stop]]
                    or not verify_separating_requests(model,plan)):
                return False
            expected=[]
            for i in range(start,stop):
                size=len(frames[i]);offset=sum(map(len,frames[:i]));origin=receipts[i].origin
                expected.append({'frame':i,'start':0,'stop':size,'event_span':[offset,offset+size],
                                 'identities':list(frames[i]),
                                 'coordinates':[[origin[0]+j,*origin[1:]] for j in range(size)]})
            if canonical(expected) != canonical(row['occurrences']):
                return False
        contexts=epochs[-1]['plan']['contexts']
        result={'status':'OBSERVATION_COMPATIBLE' if contexts else 'UNMODELED_RESPONSE',
                'epoch':len(epochs)-1,'contexts':contexts}
        return canonical(certificate['result']) == canonical(result)
    except (KeyError, IndexError, TypeError, ValueError, AttributeError):
        return False

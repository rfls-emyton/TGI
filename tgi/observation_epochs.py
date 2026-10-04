"""Complete source-local measurements without an assumed persistent context."""
from .identity import decode
from .incidence import _endpoint
from .organization_snapshot import snapshot
from .separation import separating_requests
from .separation_check import verify_separating_requests


def certify_observation_epochs(model, acquisition, source, boundaries):
    model = snapshot(model)
    history = snapshot(acquisition)
    if not isinstance(source, str) or not source:
        raise ValueError('Source required')
    frames = history.episodes[source][0]
    if (not isinstance(boundaries, (list, tuple)) or len(boundaries) < 2
            or any(type(v) is not int for v in boundaries)
            or boundaries[0] != 0 or boundaries[-1] != len(frames)
            or any(b-a < 2 for a,b in zip(boundaries, boundaries[1:]))):
        raise ValueError('Intervals must cover the entire source in order')
    if not history._alive(source):
        raise ValueError('Broken acquisition evidence')
    epochs = []
    for start, stop in zip(boundaries, boundaries[1:]):
        plan = separating_requests(model, decode(frames[start]),
                                   [decode(f) for f in frames[start+1:stop]])
        if not verify_separating_requests(model, plan):
            raise ValueError('Incomplete observation scope')
        epochs.append({'plan': plan, 'occurrences': [
            _endpoint(history, source, (i, 0, len(frames[i])))
            for i in range(start, stop)]})
    contexts = epochs[-1]['plan']['contexts']
    return {'policy': 'independent_observation_epochs_v1', 'source': source,
            'boundaries': list(boundaries), 'epochs': epochs,
            'result': {'status': 'OBSERVATION_COMPATIBLE' if contexts else 'UNMODELED_RESPONSE',
                       'epoch': len(epochs)-1, 'contexts': contexts}}

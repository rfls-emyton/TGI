"""Complete conditional histories over recorded discrete occurrences."""
from .identity import decode
from .incidence import _endpoint
from .organization_snapshot import snapshot
from .separation_check import verify_separating_requests


def _choices(plan,live):
    choices={}
    for row in plan['requests']:
        groups={tuple(g['value']):set(g['contexts'])&live for g in row['responses']}
        groups={value:ids for value,ids in groups.items() if ids}
        covered=set().union(*groups.values()) if groups else set()
        if len(live)>1 and covered==live and all(len(ids)<len(live) for ids in groups.values()):
            choices[row['query']]=groups
    return choices


def certify_acquisition_history(model,plan,acquisition,source,boundaries):
    if not verify_separating_requests(model,plan):raise ValueError('Invalid model plan')
    view=snapshot(acquisition)
    if not isinstance(source,str) or not source:raise ValueError('Source required')
    frames=view.episodes[source][0]
    if (not isinstance(boundaries,(list,tuple)) or len(boundaries)<2 or
        any(type(x) is not int for x in boundaries) or boundaries[0]!=0 or
        boundaries[-1]!=len(frames) or any(b-a<2 for a,b in zip(boundaries,boundaries[1:]))):
        raise ValueError('Intervals must cover the entire source in order')
    if not view._alive(source):raise ValueError('Broken acquisition evidence')
    live=set(range(len(plan['contexts'])));events=[];status='OBSERVED'
    for step,(start,stop) in enumerate(zip(boundaries,boundaries[1:])):
        request=decode(frames[start]);observed=[decode(f) for f in frames[start+1:stop]]
        before=sorted(live);choices=_choices(plan,live)
        if step==0:
            if request!=plan['request'] or observed!=plan['observed']:raise ValueError('Initial observation differs from plan')
        else:
            if request not in choices:raise ValueError('Request does not separate current contexts')
            live=choices[request].get(tuple(observed),set())
            status='REFINED' if live else 'UNMODELED_RESPONSE'
            if not live and step!=len(boundaries)-2:raise ValueError('History continues beyond unmodeled feedback')
        events.append({'request':request,'observed':observed,'before':before,'after':sorted(live),
                       'admissible':sorted(choices),
                       'occurrences':[_endpoint(view,source,(i,0,len(frames[i]))) for i in range(start,stop)]})
    return {'plan':plan,'source':source,'boundaries':list(boundaries),'events':events,
            'result':{'status':status,'context_indexes':sorted(live),
                      'contexts':[plan['contexts'][i] for i in sorted(live)],'next_requests':sorted(_choices(plan,live))}}

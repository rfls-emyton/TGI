"""Propose a known request against an actual context without ingesting it."""
from .identity import encode,decode
from .organization import _match,OMEGA_CRIT
from .organization_snapshot import snapshot
from .incidence import _endpoint
from .role_candidates_check import verify_role_candidates
from .role_work import RoleSearchBudget


def certify_role_proposal(model,role,acquisition,candidates,source,start,stop,*,max_search_steps=None):
    if not isinstance(source,str) or not source:raise ValueError('Source required')
    if any(type(x) is not int for x in (start,stop)):raise ValueError('Integer boundaries required')
    with RoleSearchBudget(max_search_steps).scope():
        model=snapshot(model);role=snapshot(role);history=snapshot(acquisition)
        if not verify_role_candidates(model,role,candidates):raise ValueError('Invalid candidate evidence')
        frames=history.episodes[source][0]
        if not 0<=start<stop<=len(frames) or not history._alive(source):raise ValueError('Invalid acquisition context')
        if [decode(f) for f in frames[start:stop]]!=candidates['prefix']:raise ValueError('Context differs from candidate input')
        query=encode(candidates['query']);requests=[]
        for sid,(path,_) in sorted(model.episodes.items()):
            if len(path)>=3 and path[-2]==query:
                fi=len(path)-2
                requests.append({'source':sid,'occurrence':_endpoint(model,sid,(fi,0,len(query)))})
        if not requests:raise ValueError('Request has never been observed')
        rows=[]
        for row in candidates['candidates']:
            pattern=tuple(tuple((k,tuple(v) if k=='lit' else v) for k,v in frame) for frame in row['pattern'])
            matches=_match(pattern,frames[start:stop]+(query,))
            bindings=[[[axis,list(value)] for axis,value in sorted(b.items())] for b,_ in matches]
            projected=None;gain=False
            if len(matches)==1:
                binding=matches[0][0]
                projected=[max(0,OMEGA_CRIT-len({encode(v) for v in values}|{binding[axis]}))
                           for axis,values in enumerate(row['values'])]
                gain=any(after<before for before,after in zip(row['deficit'],projected))
            rows.append({'anchor':row['anchor'],'bindings':bindings,'projected_deficit':projected,'diversity_gain':gain})
        return {'candidates':candidates,'context':{'source':source,'start':start,'stop':stop,
                'occurrences':[_endpoint(history,source,(i,0,len(frames[i]))) for i in range(start,stop)]},
                'observed_requests':requests,'projections':rows}

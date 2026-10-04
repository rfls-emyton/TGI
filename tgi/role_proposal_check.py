"""Independent occurrence and conditional diversity projection verification."""
from .identity import encode,decode
from .frame_engine import canonical
from .organization import _match,OMEGA_CRIT
from .organization_snapshot import snapshot
from .role_candidates_check import verify_role_candidates
from .role_work import RoleSearchBudget


def verify_role_proposal(model,role,acquisition,certificate,*,max_search_steps=None):
    with RoleSearchBudget(max_search_steps).scope():
        try:
            model=snapshot(model);role=snapshot(role);history=snapshot(acquisition)
            candidate=certificate['candidates'];context=certificate['context']
            if not verify_role_candidates(model,role,candidate):return False
            source=context['source'];start=context['start'];stop=context['stop']
            if not isinstance(source,str) or not source or any(type(x) is not int for x in (start,stop)):return False
            frames,_=history.episodes[source]
            if not 0<=start<stop<=len(frames) or not history._alive(source):return False
            if tuple(map(encode,candidate['prefix']))!=frames[start:stop]:return False
            # Reconstruct actual receipt coordinates, never call producer/endpoint.
            def occurrence(engine,sid,fi):
                path,receipts=engine.episodes[sid];origin=receipts[fi].origin
                offset=sum(map(len,path[:fi]));size=len(path[fi])
                return {'frame':fi,'start':0,'stop':size,'event_span':[offset,offset+size],
                        'identities':list(path[fi]),'coordinates':[[origin[0]+j,*origin[1:]] for j in range(size)]}
            requests=[]
            for sid,(path,_) in sorted(model.episodes.items()):
                if len(path)>=3 and decode(path[-2])==candidate['query']:
                    requests.append({'source':sid,'occurrence':occurrence(model,sid,len(path)-2)})
            if not requests:return False
            projections=[]
            for row in candidate['candidates']:
                pattern=tuple(tuple((kind,tuple(value) if kind=='lit' else value) for kind,value in frame) for frame in row['pattern'])
                matches=_match(pattern,frames[start:stop]+(encode(candidate['query']),))
                alternatives=[];deficits=None;gain=False
                for binding,_ in matches:
                    alternatives.append([[a,list(binding[a])] for a in sorted(binding)])
                if len(matches)==1:
                    deficits=[]
                    for axis,values in enumerate(row['values']):
                        distinct=set(map(encode,values));distinct.add(matches[0][0][axis])
                        deficits.append(max(0,OMEGA_CRIT-len(distinct)))
                    gain=any(deficits[i]<row['deficit'][i] for i in range(len(deficits)))
                projections.append({'anchor':row['anchor'],'bindings':alternatives,
                                    'projected_deficit':deficits,'diversity_gain':gain})
            expected={'candidates':candidate,'context':{'source':source,'start':start,'stop':stop,
                      'occurrences':[occurrence(history,source,i) for i in range(start,stop)]},
                      'observed_requests':requests,'projections':projections}
            return canonical(expected)==canonical(certificate)
        except (KeyError,TypeError,ValueError,IndexError,AttributeError):return False

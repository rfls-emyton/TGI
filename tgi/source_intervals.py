"""Source-local interval organization with complete raw evidence scope."""
from bisect import bisect_right
from .organization import _contrasts,_match,_joined,OMEGA_CRIT
from .compatible_joins import compatible_subsets
from .role_work import RoleSearchBudget
from .identity import encode,decode
from .incidence import _endpoint
from .organization_snapshot import snapshot

def _derive(model,query,budget):
    windows=[]
    for sid,(frames,_) in sorted(model.episodes.items()):
        if not model._alive(sid):raise ValueError('Broken source')
        for start in range(len(frames)):
            for stop in range(start+2,len(frames)+1):windows.append((sid,start,stop,frames[start:stop]))
    patterns=set();pairs=0
    by_length={}
    for i,w in enumerate(windows):by_length.setdefault(len(w[3]),[]).append(i)
    for i,a in enumerate(windows):
        indices=by_length[len(a[3])]
        for position in range(bisect_right(indices,i),len(indices)):
            budget.consume()
            b=windows[indices[position]]
            patterns.update(_contrasts(a[3],b[3]));pairs+=1
    supported={}
    for pattern in patterns:
        matches=[(i,b,loc) for i,w in enumerate(windows) if len(w[3])==len(pattern) for b,loc in _match(pattern,w[3])]
        if len({b[0] for _,b,_ in matches})>=OMEGA_CRIT:supported[pattern]=matches
    joined=set(supported)
    for i,w in enumerate(windows):
        axes=sorted({tuple(sorted((fi,a,b) for (fi,_),(a,b) in loc.items())) for matches in supported.values() for j,_,loc in matches if i==j})
        for subset in compatible_subsets(axes,budget):
            pattern=_joined(w[3],subset)
            if pattern is not None:joined.add(pattern)
    patterns=joined
    rows=[];outputs=set();endpoint_ok=True
    for pattern in sorted(patterns,key=repr):
        selected=[w for w in windows if len(w[3])==len(pattern)]
        grouped={}
        for w in selected:grouped.setdefault(w[3][:-1],[]).append(w)
        n=1+max(v for frame in pattern for kind,v in frame if kind=="axis")
        distinct=[set() for _ in range(n)];obstructions=[];supports=[];checks=[]
        for prefix,ws in sorted(grouped.items()):
            matches=_match(pattern,prefix);actual={w[3][-1] for w in ws};prediction=None
            if len(matches)==1 and set(matches[0][0])==set(range(n)):
                binding=matches[0][0];prediction=tuple(x for kind,v in pattern[-1] for x in (v if kind=='lit' else binding[v]))
                if actual=={prediction}:
                    for axis in range(n):distinct[axis].add(binding[axis])
                    for sid,start,stop,raw in ws:
                        full=_match(pattern,raw)
                        if len(full)!=1:continue
                        endpoints=[]
                        for (fi,part),(a,b) in sorted(full[0][1].items()):
                            if pattern[fi][part][0]!='axis':continue
                            ep=_endpoint(model,sid,(start+fi,a,b));frames,receipts=model.episodes[sid];origin=receipts[start+fi].origin
                            endpoint_ok &= ep['identities']==list(frames[start+fi][a:b]) and ep['coordinates']==[[origin[0]+j,*origin[1:]] for j in range(a,b)] and ep['event_span']==[sum(map(len,frames[:start+fi]))+a,sum(map(len,frames[:start+fi]))+b]
                            endpoints.append(ep)
                        supports.append({'source':sid,'start':start,'stop':stop,'endpoints':endpoints})
                else:obstructions.append(list(map(decode,prefix)))
            checks.append({'input':list(map(decode,prefix)),'observed':list(map(decode,sorted(actual))),'match_count':len(matches),'prediction':None if prediction is None else decode(prediction)})
        eligible=all(len(v)>=OMEGA_CRIT for v in distinct) and not obstructions
        inferred=[];raw_query=tuple(map(encode,query))
        if len(pattern)==len(raw_query)+1:
            matches=_match(pattern,raw_query)
            if len(matches)==1 and set(matches[0][0])==set(range(n)):
                binding=matches[0][0];inferred=[decode(tuple(x for kind,v in pattern[-1] for x in (v if kind=='lit' else binding[v])))]
                if eligible:outputs.update(inferred)
        rows.append({'pattern':pattern,'distinct':[list(map(decode,sorted(v))) for v in distinct],'obstructions':obstructions,'eligible':eligible,'supports':supports,'checks':checks,'query_predictions':inferred})
    return {'intervals':len(windows),'equal_length_pairs':pairs,'patterns':rows,'outputs':sorted(outputs),'endpoints_valid':endpoint_ok}


def certify_source_intervals(model,query,*,max_search_steps=None):
    if not isinstance(query,(list,tuple)) or not query or any(not isinstance(f,str) or not f for f in query):
        raise ValueError('Nonempty raw query frames required')
    for frame in query:encode(frame)
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        model=snapshot(model)
        inventory=_derive(model,list(query),budget)
        alternatives=inventory['outputs']
        decision={'status':'CONDITIONAL_FUNCTION' if len(alternatives)==1 else 'UNRESOLVED' if alternatives else 'NO_SUPPORTED_FUNCTION',
                  'output':alternatives if len(alternatives)==1 else [],'alternatives':alternatives}
        return {'policy':'source_interval_function_v1',
                'sources':[{'source':sid,'frames':list(map(decode,frames))} for sid,(frames,_) in sorted(model.episodes.items())],
                'query':list(query),'inventory':inventory,'decision':decision}

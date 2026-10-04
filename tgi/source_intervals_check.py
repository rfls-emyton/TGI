"""Independent exhaustive reference; no interval producer or compatible-subset calls."""
from itertools import combinations
from .organization import _contrasts,_match,_joined,OMEGA_CRIT
from .organization_snapshot import snapshot
from .identity import encode,decode
from .frame_engine import canonical
from .role_work import RoleSearchBudget


def _reconstruct(model,query,budget):
    view=snapshot(model);intervals=[]
    for sid in sorted(view.episodes):
        if not view._alive(sid):raise ValueError('Broken source')
        frames=view.episodes[sid][0]
        for begin in range(len(frames)):
            for end in range(begin+2,len(frames)+1):intervals.append((sid,begin,end,frames[begin:end]))
    candidates=set();pair_count=0
    for i in range(len(intervals)):
        for j in range(i+1,len(intervals)):
            budget.consume()
            if intervals[i][2]-intervals[i][1]==intervals[j][2]-intervals[j][1]:
                pair_count+=1;candidates.update(_contrasts(intervals[i][3],intervals[j][3]))
    supported=[]
    for pattern in candidates:
        bindings=set()
        for _,_,_,path in intervals:
            if len(path)==len(pattern):
                for assignment,_ in _match(pattern,path):bindings.add(assignment[0])
        if len(bindings)>=OMEGA_CRIT:supported.append(pattern)
    joined=set(supported)
    for _,_,_,path in intervals:
        axes=set()
        for pattern in supported:
            if len(pattern)!=len(path):continue
            for _,locations in _match(pattern,path):axes.add(tuple(sorted((fi,start,stop) for (fi,_),(start,stop) in locations.items())))
        axes=sorted(axes)
        for size in range(1,len(axes)+1):
            for subset in combinations(axes,size):
                budget.consume();pattern=_joined(path,subset)
                if pattern is not None:joined.add(pattern)
    rows=[];all_outputs=set();raw_query=tuple(map(encode,query))
    for pattern in sorted(joined,key=repr):
        count=1+max(v for frame in pattern for k,v in frame if k=='axis')
        prefixes=sorted({path[:-1] for _,_,_,path in intervals if len(path)==len(pattern)})
        values=[set() for _ in range(count)];blocked=[];supports=[];checks=[]
        for prefix in prefixes:
            relevant=[w for w in intervals if len(w[3])==len(pattern) and w[3][:-1]==prefix]
            observed=sorted({w[3][-1] for w in relevant});matches=_match(pattern,prefix);prediction=None
            if len(matches)==1 and sorted(matches[0][0])==list(range(count)):
                assignment=matches[0][0];out=[]
                for kind,value in pattern[-1]:out.extend(value if kind=='lit' else assignment[value])
                prediction=tuple(out)
                if observed!=[prediction]:blocked.append(list(map(decode,prefix)))
                else:
                    for axis in range(count):values[axis].add(assignment[axis])
                    for sid,begin,end,path in relevant:
                        full=_match(pattern,path)
                        if len(full)!=1:continue
                        frames,receipts=view.episodes[sid];points=[]
                        for (fi,part),(a,b) in sorted(full[0][1].items()):
                            if pattern[fi][part][0]!='axis':continue
                            absolute=begin+fi;origin=receipts[absolute].origin;offset=sum(len(frame) for frame in frames[:absolute])
                            points.append({'frame':absolute,'start':a,'stop':b,'event_span':[offset+a,offset+b],
                                           'identities':list(frames[absolute][a:b]),'coordinates':[[origin[0]+k,*origin[1:]] for k in range(a,b)]})
                        supports.append({'source':sid,'start':begin,'stop':end,'endpoints':points})
            checks.append({'input':list(map(decode,prefix)),'observed':list(map(decode,observed)),'match_count':len(matches),'prediction':None if prediction is None else decode(prediction)})
        eligible=not blocked and min(map(len,values))>=OMEGA_CRIT;predicted=[]
        if len(raw_query)+1==len(pattern):
            matches=_match(pattern,raw_query)
            if len(matches)==1 and sorted(matches[0][0])==list(range(count)):
                out=[]
                for kind,value in pattern[-1]:out.extend(value if kind=='lit' else matches[0][0][value])
                predicted=[decode(out)]
                if eligible:all_outputs.update(predicted)
        rows.append({'pattern':pattern,'distinct':[list(map(decode,sorted(v))) for v in values],'obstructions':blocked,'eligible':eligible,'supports':supports,'checks':checks,'query_predictions':predicted})
    return {'intervals':len(intervals),'equal_length_pairs':pair_count,'patterns':rows,'outputs':sorted(all_outputs),'endpoints_valid':True}



def verify_source_intervals(model,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        try:
            model=snapshot(model)
            if set(certificate)!={'policy','sources','query','inventory','decision'} or certificate['policy']!='source_interval_function_v1':return False
            query=certificate['query']
            if not isinstance(query,list) or not query or any(not isinstance(f,str) or not f for f in query):return False
            for frame in query:encode(frame)
            sources=[{'source':sid,'frames':list(map(decode,frames))} for sid,(frames,_) in sorted(model.episodes.items())]
            if canonical(sources)!=canonical(certificate['sources']):return False
            expected=_reconstruct(model,query,budget)
            if canonical(expected)!=canonical(certificate['inventory']):return False
            alternatives=expected['outputs'];status='NO_SUPPORTED_FUNCTION';output=[]
            if len(alternatives)==1:status='CONDITIONAL_FUNCTION';output=list(alternatives)
            elif alternatives:status='UNRESOLVED'
            return canonical(certificate['decision'])==canonical({'status':status,'output':output,'alternatives':alternatives})
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

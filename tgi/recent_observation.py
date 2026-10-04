"""Most recent compatible source-local contexts, with complete witness checks."""
from itertools import product
from contextvars import ContextVar
from .identity import encode,decode
from .frame_engine import canonical
from .organization import _match
from .organization_snapshot import snapshot
from .organization_check import verify_resolution,verify_refusal
from .observation_point import _validate
from .incidence import _endpoint


ACTIVE_TEMPORAL_CANDIDATES=ContextVar('tgi_temporal_candidates',default=None)


def _candidate_step():
    budget=ACTIVE_TEMPORAL_CANDIDATES.get()
    if budget is not None:budget.consume()


def _latest_context(pattern,frames,stop,query):
    n=len(pattern)-2
    if not 0<=n<=stop:return None
    if n==0:return () if _match(pattern,(query,)) else None
    pools=[]
    for part in pattern[:n]:
        pool=[i for i in range(stop) if _match((part,pattern[n]),(frames[i],query))]
        if not pool:return None
        pools.append(pool)
    indexes=[0]*n
    stack=[iter(reversed(pools[-1]))]
    while stack:
        position=n-len(stack)
        candidate=next(stack[-1],None)
        if candidate is None:
            stack.pop();continue
        upper=stop if position==n-1 else indexes[position+1]
        if candidate>=upper or candidate<position:continue
        indexes[position]=candidate
        suffix=tuple(frames[i] for i in indexes[position:])+(query,)
        if not _match(pattern[position:n+1],suffix):continue
        if position==0:return tuple(indexes)
        stack.append(iter(reversed(pools[position-1])))
    return None


def _select(engine,frames,stop,query):
    entries=dict(engine.organizations)
    entries.update({a:h for a,(h,_) in engine.rejected_organizations.items()})
    selected={};eligible=False
    for anchor,h in sorted(entries.items()):
        n=len(h.pattern)-2
        if not 0<=n<=stop:continue
        eligible=True
        best=_latest_context(h.pattern,frames,stop,query)
        if best is not None:selected.setdefault(best,[]).append(anchor)
    return eligible,selected


def resolve_recent_at(engine,source,stop,query):
    _validate(engine,source,stop,query);engine=snapshot(engine)
    frames=engine.episodes[source][0]
    certificate={'point':{'source':source,'stop':stop,'event_offset':sum(map(len,frames[:stop]))},
                 'query':query,'search':[], 'result':{'status':'INCOMPLETE','output':[],'candidates':[]}}
    if not engine._alive(source):return certificate
    eligible,selected=_select(engine,frames,stop,encode(query))
    outputs=set();uncertain=False;broken=False
    for indexes,anchors in sorted(selected.items()):
        prefix=[decode(frames[i]) for i in indexes]
        r=engine.resolve(prefix+[query],terminal_only=True)
        if r['status']=='RESOLVED':
            outputs.add(tuple(r['output']));r={k:r[k] for k in ('status','output','proofs')}
        uncertain |= r['status']=='AMBIGUOUS'
        broken |= r['status']=='INCOMPLETE'
        certificate['search'].append({'frames':list(indexes),'anchors':anchors,'prefix':prefix,
            'occurrences':[_endpoint(engine,source,(i,0,len(frames[i]))) for i in indexes], 'resolution':r})
    status='INCOMPLETE' if broken or not eligible else 'CONFLICT' if len(outputs)>1 else 'AMBIGUOUS' if uncertain else 'RESOLVED' if outputs else 'NO_PATH'
    certificate['result']={'status':status,'output':list(next(iter(outputs))) if status=='RESOLVED' else [],'candidates':[list(x) for x in sorted(outputs)]}
    return certificate


def _checked_latest(pattern,frames,stop,query):
    """Independent descending Cartesian scan; first complete match is maximal."""
    n=len(pattern)-2
    if not 0<=n<=stop:return None
    pools=[]
    for position in reversed(range(n)):
        permitted=[]
        for i in reversed(range(stop)):
            _candidate_step()
            if _match((pattern[position],pattern[n]),(frames[i],query)):
                permitted.append(i)
        if not permitted:return None
        pools.append(permitted)
    for reversed_indexes in product(*pools):
        _candidate_step()
        indexes=tuple(reversed(reversed_indexes))
        if any(a>=b for a,b in zip(indexes,indexes[1:])):continue
        raw=tuple(frames[i] for i in indexes)+(query,)
        if _match(pattern,raw):return indexes
    return None


def verify_recent_at(engine,certificate):
    try:
        if engine._dirty or set(certificate)!={'point','query','search','result'}:return False
        point=certificate['point'];source=point['source'];stop=point['stop'];query=certificate['query']
        _validate(engine,source,stop,query);engine=snapshot(engine)
        if not engine._alive(source):return False
        frames,receipts=engine.episodes[source]
        if canonical(point)!=canonical({'source':source,'stop':stop,'event_offset':sum(len(f) for f in frames[:stop])}):return False
        entries=[(a,h) for a,h in engine.organizations.items()]
        entries += [(a,h) for a,(h,_) in engine.rejected_organizations.items()]
        best_by_anchor={};eligible=False;encoded=encode(query)
        for anchor,h in entries:
            n=len(h.pattern)-2
            if n<0 or n>stop:continue
            eligible=True
            indexes=_checked_latest(h.pattern,frames,stop,encoded)
            if indexes is not None:best_by_anchor[anchor]=indexes
        selected={}
        for anchor,indexes in sorted(best_by_anchor.items()):selected.setdefault(indexes,[]).append(anchor)
        rows=certificate['search']
        if not eligible or len(rows)!=len(selected):return False
        outputs=set();uncertain=False
        for row,(indexes,anchors) in zip(rows,sorted(selected.items())):
            if set(row)!={'frames','anchors','prefix','occurrences','resolution'}:return False
            prefix=[decode(frames[i]) for i in indexes];endpoints=[]
            for i in indexes:
                offset=sum(len(f) for f in frames[:i]);size=len(frames[i]);origin=receipts[i].origin
                endpoints.append({'frame':i,'start':0,'stop':size,'event_span':[offset,offset+size],
                    'identities':list(frames[i]),'coordinates':[[origin[0]+j,*origin[1:]] for j in range(size)]})
            expected={'frames':list(indexes),'anchors':anchors,'prefix':prefix,'occurrences':endpoints}
            if canonical({k:row[k] for k in expected})!=canonical(expected):return False
            r=row['resolution'];trigger=prefix+[query]
            if r['status']=='RESOLVED':
                if set(r)!={'status','output','proofs'} or not verify_resolution(engine,trigger,r,terminal_only=True):return False
                outputs.add(tuple(r['output']))
            elif r['status'] in ('NO_PATH','AMBIGUOUS'):
                if not verify_refusal(engine,trigger,r,terminal_only=True):return False
                uncertain |= r['status']=='AMBIGUOUS'
            else:return False
        status='CONFLICT' if len(outputs)>1 else 'AMBIGUOUS' if uncertain else 'RESOLVED' if outputs else 'NO_PATH'
        return canonical(certificate['result'])==canonical({'status':status,'output':list(next(iter(outputs))) if status=='RESOLVED' else [],'candidates':[list(o) for o in sorted(outputs)]})
    except (KeyError,IndexError,TypeError,ValueError,AttributeError):return False

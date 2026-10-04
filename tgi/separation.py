"""Choose observed requests that separate complete sets of raw predictions."""
from .identity import encode,decode
from .organization import _match
from .organization_snapshot import snapshot
from .ask_certificate import certify_ask,verify_ask_certificate


def _finite(engine,prefix,result,terminal_only=False):
    raw=tuple(encode(f) for f in prefix)
    for h in engine.organizations.values():
        if len(raw)>=len(h.pattern) or (terminal_only and len(h.pattern)!=len(raw)+1):continue
        if any(len(b)!=len(h.diversity) for b,_ in _match(h.pattern,raw)):return False
    return result['status'] in ('RESOLVED','NO_PATH') or (result['status']=='AMBIGUOUS' and bool(result['candidates']))


def _values(result):
    return [result['output']] if result['status']=='RESOLVED' else result.get('candidates',[])


def separating_requests(engine,request,observed):
    encode(request)
    if not request or not isinstance(observed,(list,tuple)) or not observed:raise ValueError('Nonempty raw request and response required')
    for frame in observed:
        encode(frame)
        if not frame:raise ValueError('Empty response frame')
    result={'request':request,'observed':list(observed),'scope':None,'contexts':[],'requests':[],
            'result':{'status':'INCOMPLETE','requests':[]}}
    if engine._dirty:return result
    engine=snapshot(engine)
    if not all(engine._alive(s) for s in engine.episodes):return result
    scope=certify_ask(engine,request);result['scope']=scope
    if not verify_ask_certificate(engine,scope):return result
    contexts=[]
    for row in scope['search']:
        r=row['resolution']
        if not _finite(engine,row['prefix']+[request],r):return result
        if list(observed) in _values(r):contexts.append(row['prefix'])
    result['contexts']=contexts
    queries=sorted({decode(frames[-2]) for frames,_ in engine.episodes.values() if len(frames)>=2})
    chosen=[]
    for query in queries:
        predictions=[];groups={};complete=True
        for i,prefix in enumerate(contexts):
            r=engine.resolve(prefix+[query],terminal_only=True)
            if r['status'] not in ('RESOLVED','NO_PATH','AMBIGUOUS'):return result
            finite=_finite(engine,prefix+[query],r,True)
            values=_values(r) if finite else []
            complete &= finite and bool(values)
            if r['status']=='RESOLVED':r={k:r[k] for k in ('status','output','proofs')}
            predictions.append(r)
            for value in values:groups.setdefault(tuple(value),[]).append(i)
        separates=len(contexts)>1 and complete and all(len(ids)<len(contexts) for ids in groups.values())
        result['requests'].append({'query':query,'predictions':predictions,
            'responses':[{'value':list(v),'contexts':ids} for v,ids in sorted(groups.items())],'separates':separates})
        if separates:chosen.append(query)
    result['result']={'status':'SEPARATING' if chosen else 'NO_SEPARATOR','requests':chosen}
    return result


def refine_separation(engine,certificate,request,observed):
    """Consume a new raw response conditionally; never invent a world identity."""
    from .separation_check import verify_separating_requests
    encode(request)
    if not isinstance(observed,(list,tuple)) or not observed:raise ValueError('Nonempty raw response required')
    for frame in observed:
        encode(frame)
        if not frame:raise ValueError('Empty response frame')
    if not verify_separating_requests(engine,certificate):raise ValueError('Invalid or stale separation certificate')
    if request not in certificate['result']['requests']:raise ValueError('Request is not an admitted separator')
    row=next(r for r in certificate['requests'] if r['query']==request)
    indexes=next((r['contexts'] for r in row['responses'] if r['value']==list(observed)),[])
    return {'separation':certificate,'request':request,'observed':list(observed),
            'result':{'status':'REFINED' if indexes else 'UNMODELED_RESPONSE',
                      'context_indexes':list(indexes),'contexts':[certificate['contexts'][i] for i in indexes]}}

"""Independent completeness and strict-reduction check for raw requests."""
from .identity import encode,decode
from .organization import _match
from .organization_snapshot import snapshot
from .ask_certificate import verify_ask_certificate,_verify_ask_certificate_view
from .organization_check import verify_resolution,verify_refusal,_verify_refusal_view
from .frame_engine import canonical


def verify_separating_requests(engine,certificate):
    try:
        if engine._dirty or set(certificate)!={'request','observed','scope','contexts','requests','result'}:return False
        engine=snapshot(engine)
        if not all(engine._alive(s) for s in engine.episodes):return False
        request=certificate['request'];encode(request)
        observed=certificate['observed']
        if not request or not isinstance(observed,list) or not observed:return False
        for value in observed:
            encode(value)
            if not value:return False
        scope=certificate['scope']
        if scope['query']!=request or not _verify_ask_certificate_view(engine,scope):return False

        def possibilities(prefix,r,terminal):
            raw=tuple(encode(f) for f in prefix)
            for h in engine.organizations.values():
                if len(raw)>=len(h.pattern) or (terminal and len(h.pattern)!=len(raw)+1):continue
                for binding,_ in _match(h.pattern,raw):
                    if set(binding)!=set(range(len(h.diversity))):return None
            if r['status']=='RESOLVED':return {tuple(r['output'])}
            if r['status']=='NO_PATH':return set()
            if r['status']=='AMBIGUOUS' and r['candidates']:return {tuple(x) for x in r['candidates']}
            return None

        contexts=[]
        for row in scope['search']:
            values=possibilities(row['prefix']+[request],row['resolution'],False)
            if values is None:return False
            if tuple(observed) in values:contexts.append(row['prefix'])
        if canonical(contexts)!=canonical(certificate['contexts']):return False
        queries=sorted({decode(frames[-2]) for frames,_ in engine.episodes.values() if len(frames)>=2})
        if len(certificate['requests'])!=len(queries):return False
        chosen=[]
        for row,query in zip(certificate['requests'],queries):
            if set(row)!={'query','predictions','responses','separates'} or row['query']!=query:return False
            if len(row['predictions'])!=len(contexts):return False
            groups={};complete=True
            for i,(prefix,r) in enumerate(zip(contexts,row['predictions'])):
                trigger=prefix+[query]
                if r['status']=='RESOLVED':
                    if set(r)!={'status','output','proofs'} or not verify_resolution(engine,trigger,r,terminal_only=True):return False
                elif r['status'] in ('NO_PATH','AMBIGUOUS'):
                    if not _verify_refusal_view(engine,trigger,r,terminal_only=True):return False
                else:return False
                values=possibilities(trigger,r,True)
                if not values:complete=False
                for value in values or ():groups.setdefault(value,[]).append(i)
            expected=[{'value':list(v),'contexts':ids} for v,ids in sorted(groups.items())]
            separates=len(contexts)>1 and complete and all(len(ids)<len(contexts) for ids in groups.values())
            if type(row['separates']) is not bool or row['separates']!=separates or canonical(row['responses'])!=canonical(expected):return False
            if separates:chosen.append(query)
        return canonical(certificate['result'])==canonical({'status':'SEPARATING' if chosen else 'NO_SEPARATOR','requests':chosen})
    except (KeyError,TypeError,ValueError,IndexError,AttributeError):return False


def verify_refinement(engine,certificate):
    try:
        if set(certificate)!={'separation','request','observed','result'}:return False
        plan=certificate['separation']
        if not verify_separating_requests(engine,plan):return False
        query=certificate['request'];encode(query)
        observed=certificate['observed']
        if not isinstance(observed,list) or not observed:return False
        for value in observed:
            encode(value)
            if not value:return False
        if query not in plan['result']['requests']:return False
        retained=[]
        row=next(r for r in plan['requests'] if r['query']==query)
        for i,r in enumerate(row['predictions']):
            outcomes=[r['output']] if r['status']=='RESOLVED' else r['candidates']
            if observed in outcomes:retained.append(i)
        if len(retained)>=len(plan['contexts']):return False
        expected={'status':'REFINED' if retained else 'UNMODELED_RESPONSE',
                  'context_indexes':retained,'contexts':[plan['contexts'][i] for i in retained]}
        return canonical(certificate['result'])==canonical(expected)
    except (KeyError,TypeError,ValueError,IndexError,AttributeError,StopIteration):return False

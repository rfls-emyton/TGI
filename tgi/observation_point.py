"""Resolution bound to observed source-local event windows."""
from .identity import encode, decode
from .frame_engine import canonical
from .incidence import _endpoint
from .organization_snapshot import snapshot
from .organization_check import verify_resolution, verify_refusal


def _validate(engine, source, stop, query):
    if not isinstance(source, str) or type(stop) is not int or stop < 0:
        raise ValueError('Source and nonnegative integer boundary required')
    encode(query)
    if not query:
        raise ValueError('Nonempty query required')
    if source not in engine.episodes:
        raise KeyError(source)
    if stop > len(engine.episodes[source][0]):
        raise ValueError('Boundary outside observed episode')


def resolve_at(engine, source, stop, query):
    _validate(engine, source, stop, query)
    engine = snapshot(engine)
    frames = engine.episodes[source][0]
    point = {'source':source, 'stop':stop, 'event_offset':sum(map(len,frames[:stop]))}
    result = {'point':point, 'query':query, 'search':[],
              'result':{'status':'INCOMPLETE','output':[],'candidates':[]}}
    if not engine._alive(source):
        return result
    hypotheses = list(engine.organizations.values()) + [h for h,_ in engine.rejected_organizations.values()]
    lengths = sorted({len(h.pattern)-2 for h in hypotheses if 0<=len(h.pattern)-2<=stop})
    outputs=set();uncertain=False;broken=False
    for count in lengths:
        start=stop-count
        prefix=[decode(f) for f in frames[start:stop]]
        proof=engine.resolve(prefix+[query], terminal_only=True)
        if proof['status']=='RESOLVED':
            outputs.add(tuple(proof['output']))
            proof={k:proof[k] for k in ('status','output','proofs')}
        uncertain |= proof['status']=='AMBIGUOUS'
        broken |= proof['status']=='INCOMPLETE'
        result['search'].append({'start':start,'prefix':prefix,
            'occurrences':[_endpoint(engine,source,(i,0,len(frames[i]))) for i in range(start,stop)],
            'resolution':proof})
    status=('INCOMPLETE' if broken or not lengths else 'CONFLICT' if len(outputs)>1 else
            'AMBIGUOUS' if uncertain else 'RESOLVED' if outputs else 'NO_PATH')
    result['result']={'status':status,'output':list(next(iter(outputs))) if status=='RESOLVED' else [],
                      'candidates':[list(o) for o in sorted(outputs)]}
    return result


def verify_at(engine, certificate):
    try:
        if engine._dirty or set(certificate)!={'point','query','search','result'}:
            return False
        point=certificate['point'];source=point['source'];stop=point['stop'];query=certificate['query']
        _validate(engine,source,stop,query)
        engine=snapshot(engine)
        if not engine._alive(source):return False
        frames,receipts=engine.episodes[source]
        expected_point={'source':source,'stop':stop,'event_offset':sum(len(f) for f in frames[:stop])}
        if canonical(point)!=canonical(expected_point):return False
        lengths={len(h.pattern)-2 for h in engine.organizations.values()}
        lengths.update(len(h.pattern)-2 for h,_ in engine.rejected_organizations.values())
        lengths=sorted(n for n in lengths if 0<=n<=stop)
        if not lengths or len(certificate['search'])!=len(lengths):return False
        outputs=set();uncertain=False
        for count,row in zip(lengths,certificate['search']):
            if set(row)!={'start','prefix','occurrences','resolution'}:return False
            start=stop-count;prefix=[decode(f) for f in frames[start:stop]]
            endpoints=[]
            for i in range(start,stop):
                origin=receipts[i].origin;offset=sum(len(f) for f in frames[:i]);size=len(frames[i])
                endpoints.append({'frame':i,'start':0,'stop':size,'event_span':[offset,offset+size],
                    'identities':list(frames[i]),
                    'coordinates':[[origin[0]+j,*origin[1:]] for j in range(size)]})
            expected={'start':start,'prefix':prefix,'occurrences':endpoints}
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
        expected={'status':status,'output':list(next(iter(outputs))) if status=='RESOLVED' else [],
                  'candidates':[list(o) for o in sorted(outputs)]}
        return canonical(certificate['result'])==canonical(expected)
    except (KeyError,IndexError,TypeError,ValueError,AttributeError):
        return False

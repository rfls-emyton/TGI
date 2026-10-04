"""Complete prefix-scope certificate for raw stored-context search."""
from .identity import encode,decode
from .frame_engine import canonical
from .organization_snapshot import snapshot
from .organization_check import verify_resolution,verify_refusal,_verify_refusal_view


def certify_ask(engine, raw):
    encode(raw)
    if not raw:raise ValueError('Empty query')
    view=snapshot(engine)
    lengths={len(h.pattern)-2 for h in view.organizations.values()}
    lengths.update(len(h.pattern)-2 for h,_ in view.rejected_organizations.values())
    prefixes={():[]} if 0 in lengths else {}
    for sid,(frames,_) in view.episodes.items():
        for count in lengths:
            if 0<count<=len(frames):prefixes.setdefault(tuple(decode(f) for f in frames[:count]),[]).append(sid)
    rows=[];outputs=set();uncertain=False;broken=False
    for prefix,sources in sorted(prefixes.items()):
        r=view.resolve(prefix+(raw,))
        if r['status']!='NO_PATH':
            live=[sid for sid in sources if view._alive(sid)]
            if sources and not live:broken=True
            else:
                broken |= r['status']=='INCOMPLETE'
                uncertain |= r['status']=='AMBIGUOUS'
                if r['status']=='RESOLVED':outputs.add(tuple(r['output']))
        if r['status']=='RESOLVED':r={k:r[k] for k in ('status','output','proofs')}
        rows.append({'prefix':list(prefix),'sources':sorted(sources),'resolution':r})
    status='INCOMPLETE' if broken else 'CONFLICT' if len(outputs)>1 else 'AMBIGUOUS' if uncertain else 'RESOLVED' if outputs else 'NO_PATH'
    result={'status':status,'output':list(next(iter(outputs))) if status=='RESOLVED' else [],'candidates':[list(x) for x in sorted(outputs)]}
    return {'query':raw,'result':result,'search':rows}


def _verify_ask_certificate_view(engine, certificate):
    from .organization_snapshot import _Snapshot
    try:
        if type(engine) is not _Snapshot or engine._dirty or set(certificate)!={'query','result','search'}:return False
        raw=certificate['query'];encode(raw)
        if not raw:return False
        sizes=set()
        for h in engine.organizations.values():sizes.add(len(h.pattern)-2)
        for h,_ in engine.rejected_organizations.values():sizes.add(len(h.pattern)-2)
        scope={():set()} if 0 in sizes else {}
        for sid,(frames,_) in engine.episodes.items():
            for n in sizes:
                if 0<n<=len(frames):scope.setdefault(tuple(decode(f) for f in frames[:n]),set()).add(sid)
        rows=certificate['search']
        if len(rows)!=len(scope):return False
        outputs=set();uncertain=False
        for row,(prefix,sources) in zip(rows,sorted(scope.items())):
            if set(row)!={'prefix','sources','resolution'}:return False
            if canonical(row['prefix'])!=canonical(list(prefix)) or canonical(row['sources'])!=canonical(sorted(sources)):return False
            if not all(engine._alive(sid) for sid in sources):return False
            r=row['resolution'];status=r['status'];trigger=list(prefix)+[raw]
            if status=='RESOLVED':
                if set(r)!={'status','output','proofs'} or not verify_resolution(engine,trigger,r):return False
                outputs.add(tuple(r['output']))
            elif status in ('NO_PATH','AMBIGUOUS'):
                if not _verify_refusal_view(engine,trigger,r):return False
                uncertain |= status=='AMBIGUOUS'
            else:return False
        status='CONFLICT' if len(outputs)>1 else 'AMBIGUOUS' if uncertain else 'RESOLVED' if outputs else 'NO_PATH'
        expected={'status':status,'output':list(next(iter(outputs))) if status=='RESOLVED' else [],'candidates':[list(x) for x in sorted(outputs)]}
        return canonical(certificate['result'])==canonical(expected)
    except (KeyError,IndexError,TypeError,ValueError,AttributeError):return False


def verify_ask_certificate(engine, certificate):
    """Fresh public evidence boundary; never reuse a caller's cached admission."""
    try:
        return _verify_ask_certificate_view(snapshot(engine), certificate)
    except (KeyError, IndexError, TypeError, ValueError, AttributeError):
        return False

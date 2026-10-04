"""Conditional whole-path orientation inferred within a declared line-isometry family.

Original directed crystals are never traversed backward or mutated. Query output
is an explicit index transport with one unchanged NMU ID per output character.
"""
from .organization_snapshot import snapshot
from .role_work import RoleSearchBudget
from .organization import OMEGA_CRIT
from tgi.identity import encode,decode
from tgi.frame_engine import canonical
from tgi.incidence import _endpoint


def _produce(m,query,budget):
    q=encode(query)
    if not q:raise ValueError('Nonempty query required')
    if m._dirty:raise ValueError('Invalid original evidence')
    allowed={1,-1};rows=[];distinct=set()
    for s,(frames,_) in sorted(m.episodes.items()):
        budget.consume()
        if not m._alive(s):raise ValueError('Broken original evidence')
        if len(frames)!=2:raise ValueError('Paired-path scope required')
        a,b=frames;distinct.add(a);maps=[]
        for direction in (-1,1):
            budget.consume()
            for _ in a:budget.consume()
            mapping=[i if direction==1 else len(a)-1-i for i in range(len(a))]
            if len(a)==len(b) and all(a[i]==b[j] for i,j in enumerate(mapping)):
                maps.append(dict(direction=direction,mapping=mapping))
        allowed &= {r['direction'] for r in maps}
        rows.append(dict(source=s,frames=[decode(a),decode(b)],occurrences=[_endpoint(m,s,(i,0,len(f))) for i,f in enumerate(frames)],maps=maps))
    status='CONFLICT' if not allowed else 'INCOMPLETE' if len(distinct)<OMEGA_CRIT else 'AMBIGUOUS' if len(allowed)!=1 else 'CONDITIONAL_ISOMETRY'
    order=[]
    if status=='CONDITIONAL_ISOMETRY':
        for _ in q:budget.consume()
        direction=next(iter(allowed));order=list(range(len(q))) if direction==1 else list(range(len(q)-1,-1,-1))
    return dict(query=query,sources=rows,directions=sorted(allowed),diversity=len(distinct),status=status,output=decode(tuple(q[i] for i in order)) if order else None,provenance=[dict(query_index=i,identity=q[i]) for i in order])


def _check(m,query,c,budget):
    try:
        q=encode(query)
        if not q or m._dirty:return False
        if set(c)!={'query','sources','directions','diversity','status','output','provenance'} or c['query']!=query:return False
        rows=[];forward=True;backward=True;distinct=set()
        for s,(frames,receipts) in sorted(m.episodes.items()):
            budget.consume()
            if not m._alive(s):return False
            if len(frames)!=2:return False
            a,b=frames;distinct.add(a);same=len(a)==len(b)
            for _ in range(len(a)+len(b)):budget.consume()
            f=same and all(b[k]==a[k] for k in range(len(b)));r=same and all(b[k]==a[len(a)-1-k] for k in range(len(b)));forward &= f;backward &= r
            points=[]
            for fi,frame in enumerate(frames):
                n=len(frame);origin=receipts[fi].origin;off=sum(map(len,frames[:fi]));points.append(dict(frame=fi,start=0,stop=n,event_span=[off,off+n],identities=list(frame),coordinates=[[origin[0]+i,*origin[1:]] for i in range(n)]))
            maps=[]
            if r:maps.append(dict(direction=-1,mapping=[len(a)-1-i for i in range(len(a))]))
            if f:maps.append(dict(direction=1,mapping=list(range(len(a)))))
            rows.append(dict(source=s,frames=[decode(a),decode(b)],occurrences=points,maps=maps))
        directions=([-1] if backward else [])+([1] if forward else []);status='CONFLICT' if not directions else 'INCOMPLETE' if len(distinct)<OMEGA_CRIT else 'AMBIGUOUS' if len(directions)!=1 else 'CONDITIONAL_ISOMETRY';order=[]
        if status=='CONDITIONAL_ISOMETRY':
            for _ in q:budget.consume()
            order=[i if directions[0]==1 else len(q)-1-i for i in range(len(q))]
        expected=dict(query=query,sources=rows,directions=directions,diversity=len(distinct),status=status,output=decode(tuple(q[i] for i in order)) if order else None,provenance=[dict(query_index=i,identity=q[i]) for i in order])
        return canonical(c)==canonical(expected)
    except (TypeError,ValueError,IndexError,KeyError,AttributeError):return False


def certify_path_isometry(model,query,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        return dict(policy='whole_path_isometry_v1',threshold=OMEGA_CRIT,**_produce(snapshot(model),query,budget))


def verify_path_isometry(model,query,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        try:
            if not isinstance(certificate,dict) or set(certificate)!={'policy','threshold','query','sources','directions','diversity','status','output','provenance'} or certificate['policy']!='whole_path_isometry_v1' or type(certificate['threshold']) is not int or certificate['threshold']!=OMEGA_CRIT:return False
            core={k:v for k,v in certificate.items() if k not in ('policy','threshold')}
            return _check(snapshot(model),query,core,budget)
        except (TypeError,ValueError,KeyError,IndexError,AttributeError):return False

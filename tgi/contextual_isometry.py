"""Contextual interval orientation induced from complete raw paired evidence."""
from tgi.identity import encode,decode
from tgi.incidence import _endpoint
from tgi.organization import OMEGA_CRIT

def region(h,x):
    a,b,_,_,_=h;stop=len(x)-len(b)
    return (len(a),stop) if stop>len(a) and x[:len(a)]==a and (not b or x[stop:]==b) else None

def apply(h,x):
    r=region(h,x)
    if r is None:return None
    a,b,c,d,sign=h;z=x[r[0]:r[1]]
    return c+(z if sign==1 else z[::-1])+d

def derive(a,b,budget):
    found=set()
    for start in range(len(a)):
      for j in range(len(b)):
        for sign in (-1,1):
            k=0
            while j+k<len(b) and 0<=start+sign*k<len(a):
                budget.consume()
                if a[start+sign*k]!=b[j+k]:break
                k+=1
                lo=start if sign==1 else start-k+1
                hi=start+k if sign==1 else start+1
                found.add((a[:lo],a[hi:],b[:j],b[j+k:],sign))
    return found


def _produce(m,query,budget):
    q=encode(query)
    if not q or m._dirty:raise ValueError('Invalid raw evidence/query')
    raw=[];hypotheses=set()
    for s,(frames,_) in sorted(m.episodes.items()):
        budget.consume()
        if not m._alive(s):raise ValueError('Invalid original evidence')
        if len(frames)!=2:raise ValueError('Paired raw frames required')
        a,b=frames;hypotheses.update(derive(a,b,budget));raw.append(dict(source=s,frames=[decode(a),decode(b)],occurrences=[_endpoint(m,s,(i,0,len(f))) for i,f in enumerate(frames)]))
    rows=[];answers=set()
    for h in sorted(hypotheses):
        supports=[];contradictions=[];values=set()
        for s,(frames,_) in sorted(m.episodes.items()):
            budget.consume()
            a,b=frames;r=region(h,a)
            if r is None:continue
            if apply(h,a)==b:supports.append(s);values.add(a[r[0]:r[1]])
            else:contradictions.append(s)
        budget.consume()
        eligible=len(values)>=OMEGA_CRIT and not contradictions;result=apply(h,q)
        if eligible and result is not None:answers.add(result)
        rows.append(dict(boundaries=[list(x) for x in h[:4]],orientation=h[4],supports=supports,contradictions=contradictions,diversity=len(values),eligible=eligible,query_output=decode(result) if eligible and result is not None else None))
    outputs=sorted(map(decode,answers));return dict(query=query,sources=raw,candidates=rows,outputs=outputs,status='CONDITIONAL_OUTPUT' if len(outputs)==1 else 'AMBIGUOUS_OUTPUT' if outputs else 'UNRESOLVED',output=outputs[0] if len(outputs)==1 else None)


def certify_contextual_isometry(model,query,*,max_search_steps=None):
    from .organization_snapshot import snapshot
    from .role_work import RoleSearchBudget
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        return dict(policy='contextual_interval_isometry_v1',threshold=OMEGA_CRIT,**_produce(snapshot(model),query,budget))

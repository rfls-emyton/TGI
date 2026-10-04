"""Independent exhaustive reference; no calls to candidate producer/helpers."""
from itertools import product
from tgi.identity import encode,decode
from tgi.organization import OMEGA_CRIT

def _expected(m,query,budget):
    q=encode(query)
    if not q or m._dirty:raise ValueError('Invalid evidence')
    inventory=[];hs=set()
    for sid,(frames,receipts) in sorted(m.episodes.items()):
        budget.consume()
        if not m._alive(sid):raise ValueError('Invalid original evidence')
        if len(frames)!=2:raise ValueError('Invalid arity')
        x,y=frames
        for length in range(1,min(len(x),len(y))+1):
          for i,j in product(range(len(x)-length+1),range(len(y)-length+1)):
            budget.consume()
            f=all(y[j+k]==x[i+k] for k in range(length));r=all(y[j+k]==x[i+length-1-k] for k in range(length))
            for sign,ok in ((1,f),(-1,r)):
                if ok:hs.add((x[:i],x[i+length:],y[:j],y[j+length:],sign))
        points=[]
        for fi,f in enumerate(frames):
            origin=receipts[fi].origin;offset=sum(map(len,frames[:fi]));points.append(dict(frame=fi,start=0,stop=len(f),event_span=[offset,offset+len(f)],identities=list(f),coordinates=[[origin[0]+i,*origin[1:]] for i in range(len(f))]))
        inventory.append(dict(source=sid,frames=list(map(decode,frames)),occurrences=points))
    rows=[];outputs=set()
    for a,b,c,d,sign in sorted(hs):
        support=[];reject=[];distinct=set()
        for sid,(frames,_) in sorted(m.episodes.items()):
            budget.consume()
            x,y=frames;n=len(x)-len(a)-len(b)
            if n<=0 or tuple(x[:len(a)])!=a or tuple(x[len(a)+n:])!=b:continue
            z=tuple(x[len(a)+i] for i in range(n));mapped=c+tuple(z[k if sign==1 else n-1-k] for k in range(n))+d
            if y==mapped:support.append(sid);distinct.add(z)
            else:reject.append(sid)
        budget.consume()
        eligible=len(distinct)>=OMEGA_CRIT and len(reject)==0;answer=None;n=len(q)-len(a)-len(b)
        if eligible and n>0 and q[:len(a)]==a and q[len(a)+n:]==b:
            answer=decode(c+tuple(q[len(a)+(k if sign==1 else n-1-k)] for k in range(n))+d);outputs.add(answer)
        rows.append(dict(boundaries=[list(a),list(b),list(c),list(d)],orientation=sign,supports=support,contradictions=reject,diversity=len(distinct),eligible=eligible,query_output=answer))
    outputs=sorted(outputs)
    return dict(query=query,sources=inventory,candidates=rows,outputs=outputs,status='CONDITIONAL_OUTPUT' if len(outputs)==1 else 'AMBIGUOUS_OUTPUT' if outputs else 'UNRESOLVED',output=outputs[0] if len(outputs)==1 else None)


def verify_contextual_isometry(model,query,certificate,*,max_search_steps=None):
    from .organization_snapshot import snapshot
    from .role_work import RoleSearchBudget
    from .frame_engine import canonical
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        try:
            if not isinstance(certificate,dict) or type(certificate.get('threshold')) is not int:return False
            expected=dict(policy='contextual_interval_isometry_v1',threshold=OMEGA_CRIT,**_expected(snapshot(model),query,budget))
            return canonical(certificate)==canonical(expected)
        except (TypeError,ValueError,KeyError,IndexError,AttributeError):return False

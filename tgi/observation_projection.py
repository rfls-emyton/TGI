"""Witnessed one-way observation maps; original NMU identities stay distinct."""
from tgi.identity import encode,decode
from tgi.incidence import _endpoint
from tgi.organization import OMEGA_CRIT

def _produce(m,query,budget):
    q=encode(query)
    if not q or m._dirty:raise ValueError('Invalid original scope')
    sources=[];distinct=set()
    for s,(frames,_) in sorted(m.episodes.items()):
        budget.consume()
        if not m._alive(s):raise ValueError('Broken original evidence')
        if len(frames)!=2:raise ValueError('Paired views required')
        distinct.add(frames[0]);sources.append(dict(source=s,occurrences=[_endpoint(m,s,(fi,0,len(f))) for fi,f in enumerate(frames)]))
    alternatives=[]
    for direction in (-1,1):
        mapping={};witnesses={};valid=True
        for s,(frames,_) in sorted(m.episodes.items()):
            budget.consume()
            a,b=frames
            if len(a)!=len(b):valid=False;break
            for i,x in enumerate(a):
                budget.consume()
                j=i if direction==1 else len(a)-1-i;y=b[j]
                if x in mapping and mapping[x]!=y:valid=False;break
                mapping[x]=y;witnesses.setdefault((x,y),[]).append(dict(source=s,input_index=i,output_index=j))
            if not valid:break
        if valid:
            for _ in q:budget.consume()
            missing=sorted(set(q)-set(mapping));order=q if direction==1 else q[::-1]
            fibers={}
            for x,y in sorted(mapping.items()):
                budget.consume();fibers.setdefault(y,[]).append(x)
            alternatives.append(dict(direction=direction,inverse_fibers=[dict(output=y,inputs=xs) for y,xs in sorted(fibers.items())],mapping=[dict(input=x,output=y,witnesses=witnesses[x,y]) for x,y in sorted(mapping.items())],missing=missing,output=None if missing else decode(tuple(mapping[x] for x in order))))
    outputs=sorted({c['output'] for c in alternatives if c['output'] is not None})
    status='CONFLICT' if not alternatives else 'INCOMPLETE' if len(distinct)<OMEGA_CRIT else 'UNKNOWN_ID' if any(c['missing'] for c in alternatives) else 'AMBIGUOUS_OUTPUT' if len(outputs)!=1 else 'CONDITIONAL_OUTPUT'
    return dict(query=query,sources=sources,diversity=len(distinct),alternatives=alternatives,outputs=outputs,status=status,output=outputs[0] if status=='CONDITIONAL_OUTPUT' else None)


def certify_observation_projection(model,query,*,max_search_steps=None):
    from .organization_snapshot import snapshot
    from .role_work import RoleSearchBudget
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        return dict(policy='observation_projection_v1',threshold=OMEGA_CRIT,**_produce(snapshot(model),query,budget))

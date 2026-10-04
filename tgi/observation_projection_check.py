"""Independent full relation-set verifier for witnessed observation projections."""
from .identity import encode,decode
from .organization import OMEGA_CRIT
from .organization_snapshot import snapshot
from .role_work import RoleSearchBudget
from .frame_engine import canonical

def _expected(m,query,budget):
    q=encode(query)
    if not q:raise ValueError('Nonempty query required')
    sources=[];distinct=set()
    for s,(frames,receipts) in sorted(m.episodes.items()):
        budget.consume()
        if len(frames)!=2 or not m._alive(s):raise ValueError('Invalid source')
        distinct.add(frames[0]);points=[]
        for fi,f in enumerate(frames):
            origin=receipts[fi].origin;offset=sum(map(len,frames[:fi]))
            points.append(dict(frame=fi,start=0,stop=len(f),event_span=[offset,offset+len(f)],identities=list(f),coordinates=[[origin[0]+i,*origin[1:]] for i in range(len(f))]))
        sources.append(dict(source=s,occurrences=points))
    alternatives=[]
    for sign in (-1,1):
        edges={};left={};right={};equal=True
        for s,(frames,_) in sorted(m.episodes.items()):
            budget.consume();a,b=frames
            if len(a)!=len(b):equal=False;continue
            for j,y in enumerate(b):
                budget.consume();i=j if sign==1 else len(a)-1-j;x=a[i]
                left.setdefault(x,set()).add(y);right.setdefault(y,set()).add(x)
                edges.setdefault((x,y),[]).append(dict(source=s,input_index=i,output_index=j))
        if not equal or any(len(v)!=1 for v in left.values()) :continue
        mapping={x:next(iter(values)) for x,values in left.items()};missing=set();output=[]
        for k in range(len(q)):
            budget.consume();x=q[k if sign==1 else len(q)-1-k]
            if x not in mapping:missing.add(x)
            else:output.append(mapping[x])
        alternatives.append(dict(direction=sign,inverse_fibers=[dict(output=y,inputs=sorted(xs)) for y,xs in sorted(right.items())],mapping=[dict(input=x,output=y,witnesses=sorted(edges[x,y],key=lambda w:(w['source'],w['input_index']))) for x,y in sorted(mapping.items())],missing=sorted(missing),output=None if missing else decode(tuple(output))))
    outputs=sorted({c['output'] for c in alternatives if c['output'] is not None})
    status='CONFLICT' if not alternatives else 'INCOMPLETE' if len(distinct)<OMEGA_CRIT else 'UNKNOWN_ID' if any(c['missing'] for c in alternatives) else 'AMBIGUOUS_OUTPUT' if len(outputs)!=1 else 'CONDITIONAL_OUTPUT'
    return dict(query=query,sources=sources,diversity=len(distinct),alternatives=alternatives,outputs=outputs,status=status,output=outputs[0] if status=='CONDITIONAL_OUTPUT' else None)

def verify_observation_projection(model,query,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        try:
            if not isinstance(certificate,dict) or type(certificate.get('threshold')) is not int:return False
            expected=dict(policy='observation_projection_v1',threshold=OMEGA_CRIT,**_expected(snapshot(model),query,budget))
            return canonical(certificate)==canonical(expected)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

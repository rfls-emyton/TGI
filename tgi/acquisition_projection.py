from tgi.compact_measured_path import _read_count
from tgi.identity import encode,decode
from tgi.acquisition_witness import certify_acquisition_witness
from tgi.organization import OMEGA_CRIT
from tgi.frame_engine import canonical
from tgi.compact_measured_path import _decimal_count

def build(left,right,alignments,direction,budget):
    index={(a['left'],a['right'],a['direction']):k for k,a in enumerate(alignments)}
    states=[(0,())];lookup={(0,()):0};ways=[1];edges=[];cursor=0
    while cursor<len(states):
        budget.consume()
        mask,items=states[cursor];i=mask.bit_count()
        if i<len(left):
          for j in range(len(right)):
            budget.consume()
            if mask&(1<<j):continue
            aid=index.get((i,j,direction))
            if aid is None:continue
            a=alignments[aid];mapping=dict(items);valid=True
            for u,v,_,_ in a['positions']:
                budget.consume()
                if u in mapping and mapping[u]!=v:valid=False;break
                mapping[u]=v
            if not valid:continue
            state=(mask|(1<<j),tuple(sorted(mapping.items())))
            if state not in lookup:lookup[state]=len(states);states.append(state);ways.append(0)
            target=lookup[state];ways[target]+=ways[cursor];edges.append([cursor,target,aid])
        cursor+=1
    return dict(direction=direction,nodes=[dict(mask=mask,mapping=[list(p) for p in items],count=_decimal_count(ways[i])) for i,(mask,items) in enumerate(states)],edges=edges,terminals=[i for i,(mask,_) in enumerate(states) if mask.bit_count()==len(left)])

def _produce(m,measurements,left,right,query,budget):
    q=encode(query)
    if not q or not isinstance(left,list) or not isinstance(right,list) or len(set(left))!=len(left) or len(set(right))!=len(right) or set(left)&set(right) or set(left)|set(right)!=set(m.episodes):raise ValueError('Complete disjoint channels required')
    witness=certify_acquisition_witness(m,measurements);records={r['source']:r for r in witness['measurements']}
    if len(records)!=len(measurements) or set(records)!=set(m.episodes):raise ValueError('Full measurements required')
    for s,(frames,_) in m.episodes.items():
        budget.consume()
        r=records[s]
        if len(frames)!=1 or r['frame']!=0 or r['start']!=0 or r['stop']!=len(frames[0]):raise ValueError('Full single-frame scope required')
    left=sorted(left);right=sorted(right);clocks=sorted({r['clock'] for r in records.values()});enabled=len(left)==len(right) and len(clocks)==1;alignments=[];graphs=[];outcomes=[]
    if enabled:
      for i,a in enumerate(left):
       for j,b in enumerate(right):
        budget.consume()
        if max(records[a]['lower'],records[b]['lower'])>min(records[a]['upper'],records[b]['upper']):continue
        alignments.append(dict(left=i,right=j,direction=0,positions=[]));x=m.episodes[a][0][0];y=m.episodes[b][0][0]
        if len(x)!=len(y):continue
        for _ in x:budget.consume()
        for direction in (-1,1):alignments.append(dict(left=i,right=j,direction=direction,positions=[[u,y[k if direction==1 else len(x)-1-k],k,k if direction==1 else len(x)-1-k] for k,u in enumerate(x)]))
      for direction in (0,-1,1):
        graph=build(left,right,alignments,direction,budget);graphs.append(graph)
        if direction:
          for terminal in graph['terminals']:
            for _ in q:budget.consume()
            node=graph['nodes'][terminal];mapping=dict(node['mapping']);missing=sorted(set(q)-set(mapping));ids=q if direction==1 else q[::-1]
            fibers={}
            for u,v in sorted(mapping.items()):budget.consume();fibers.setdefault(v,[]).append(u)
            outcomes.append(dict(direction=direction,terminal=terminal,count=node['count'],inverse_fibers=[dict(output=v,inputs=us) for v,us in sorted(fibers.items())],missing=missing,output=None if missing else decode(tuple(mapping[u] for u in ids))))
    count=sum(_read_count(o['count']) for o in outcomes);outputs=sorted({o['output'] for o in outcomes if o['output'] is not None});distinct=len({m.episodes[s][0][0] for s in left})
    status='INCOMPLETE' if len(left)!=len(right) else 'CLOCK_UNDETERMINED' if len(clocks)!=1 else 'CONFLICT' if not count else 'INCOMPLETE' if distinct<OMEGA_CRIT else 'UNKNOWN_ID' if any(o['missing'] for o in outcomes) else 'AMBIGUOUS_OUTPUT' if len(outputs)!=1 else 'CONDITIONAL_OUTPUT'
    return dict(query=query,left=left,right=right,witness=witness,alignments=alignments,graphs=graphs,outcomes=outcomes,alternative_count=_decimal_count(count),diversity=distinct,status=status,outputs=outputs,output=outputs[0] if status=='CONDITIONAL_OUTPUT' else None)


def certify_acquisition_projection(model,measurements,left,right,query,*,max_search_steps=None):
    from .organization_snapshot import snapshot
    from .role_work import RoleSearchBudget
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        return dict(policy='acquisition_projection_v1',threshold=OMEGA_CRIT,**_produce(snapshot(model),[dict(r) for r in measurements],list(left) if isinstance(left,list) else left,list(right) if isinstance(right,list) else right,query,budget))

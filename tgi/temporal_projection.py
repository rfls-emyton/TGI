from tgi.compact_measured_path import _read_count
import copy
from tgi.acquisition_projection import certify_acquisition_projection as block_certify
from tgi.acquisition_projection_check import verify_acquisition_projection
from tgi.organization import OMEGA_CRIT
from tgi.compact_measured_path import _decimal_count

def _produce(m,r,left,right,q,budget):
    whole=block_certify(m,r,left,right,q);components=[];upper=None
    if len({x['clock'] for x in r})!=1:return dict(whole=whole,components=[],blocks=[],edges=[],prefix_counts=['0'],assignment_counts=['0'],outputs=[],status='CLOCK_UNDETERMINED',output=None)
    for record in sorted(r,key=lambda x:(x['lower'],x['upper'],x['source'])):
        budget.consume()
        if upper is None or record['lower']>upper:components.append([]);upper=record['upper']
        components[-1].append(record['source']);upper=max(upper,record['upper'])
    blocks=[];edges=[];count=len(components)
    for start in range(count):
      sources=[]
      for stop in range(start+1,count+1):
        budget.consume()
        sources+=components[stop-1];scope=sorted(sources);view=copy.copy(m);view.episodes={s:m.episodes[s] for s in scope};records=[x for x in r if x['source'] in scope];a=[s for s in left if s in scope];b=[s for s in right if s in scope];c=whole if start==0 and stop==count else block_certify(view,records,a,b,q)
        if not verify_acquisition_projection(view,records,a,b,q,c):raise ValueError('Invalid block certificate')
        index=len(blocks);blocks.append(dict(start=start,stop=stop,sources=scope,certificate=c))
        if _read_count(c['alternative_count'])>0 and c['diversity']>=OMEGA_CRIT:edges.append(index)
    ways=[1]+[0]*count;assignments=[1]+[0]*count
    for end in range(1,count+1):
        for index in edges:
            budget.consume()
            b=blocks[index]
            if b['stop']==end:ways[end]+=ways[b['start']];assignments[end]+=assignments[b['start']]*_read_count(b['certificate']['alternative_count'])
    final=[blocks[i]['certificate'] for i in edges if blocks[i]['stop']==count and ways[blocks[i]['start']]];outputs=sorted({x for c in final for x in c['outputs']});missing=any(any(o['missing'] for o in c['outcomes']) for c in final)
    status='UNRESOLVED' if not ways[-1] else 'UNKNOWN_ID' if missing else 'AMBIGUOUS_OUTPUT' if len(outputs)!=1 else 'CONDITIONAL_OUTPUT'
    return dict(whole=whole,components=components,blocks=blocks,edges=edges,prefix_counts=list(map(_decimal_count,ways)),assignment_counts=list(map(_decimal_count,assignments)),outputs=outputs,status=status,output=outputs[0] if status=='CONDITIONAL_OUTPUT' else None)


def certify_temporal_projection(model,measurements,left,right,query,*,max_search_steps=None):
    from .organization_snapshot import snapshot
    from .role_work import RoleSearchBudget
    if not isinstance(measurements,list) or any(not isinstance(x,dict) for x in measurements) or not isinstance(left,list) or not isinstance(right,list):raise ValueError('Acquisition lists required')
    records=[dict(x) for x in measurements];a=list(left);b=list(right);budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        return dict(policy='temporal_projection_dag_v1',threshold=OMEGA_CRIT,**_produce(snapshot(model),records,a,b,query,budget))

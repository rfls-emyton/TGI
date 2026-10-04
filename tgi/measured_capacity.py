from tgi.acquisition_witness import certify_acquisition_witness,verify_acquisition_witness
from tgi.organization_snapshot import snapshot
from tgi.frame_engine import canonical
from tgi.capacity_graph import certify_capacity_graph as capacity,verify_capacity_graph as check_capacity
from tgi.role_work import RoleSearchBudget

def scope(m,r,left,right,budget):
    if not isinstance(left,list) or not isinstance(right,list) or len(set(left))!=len(left) or len(set(right))!=len(right) or set(left)&set(right) or set(left)|set(right)!=set(m.episodes):raise ValueError('Channel scope')
    records={x['source']:x for x in r}
    if len(records)!=len(r) or set(records)!=set(m.episodes):raise ValueError('Measurement scope')
    for s,(frames,_) in m.episodes.items():
        budget.consume();x=records[s]
        if len(frames)!=1 or (x['frame'],x['start'],x['stop'])!=(0,0,len(frames[0])):raise ValueError('Full frame required')
    return records

def _produce(model,measurements,left,right,budget):
    m=snapshot(model);w=certify_acquisition_witness(m,measurements);r=w['measurements'];records=scope(m,r,left,right,budget);left=sorted(left);right=sorted(right)
    comparable=len({x['clock'] for x in r})==1;edges=[]
    if comparable:
        for pair in w['pairs']:
            budget.consume();a=r[pair['left']]['source'];b=r[pair['right']]['source']
            if a in right:a,b=b,a
            if a in left and b in right:edges.append([a,b])
    edges.sort()
    return dict(policy='measured_capacity_v1',left=left,right=right,witness=w,edges=edges,capacity_certificate=capacity(left,right,edges) if comparable else None,status='CAPACITY_CERTIFIED' if comparable else 'CLOCK_UNDETERMINED')

def _verify(model,measurements,left,right,c,budget):
    try:
        if set(c)!={'policy','left','right','witness','edges','capacity_certificate','status'} or c['policy']!='measured_capacity_v1':return False
        m=snapshot(model)
        if not verify_acquisition_witness(m,measurements,c['witness']):return False
        records=scope(m,measurements,left,right,budget);left=sorted(left);right=sorted(right)
        if c['left']!=left or c['right']!=right:return False
        comparable=len({x['clock'] for x in measurements})==1;edges=[]
        if comparable:
            for a in left:
                for b in right:
                    budget.consume()
                    if records[a]['lower']<=records[b]['upper'] and records[b]['lower']<=records[a]['upper']:edges.append([a,b])
        if canonical(c['edges'])!=canonical(edges):return False
        if not comparable:return c['capacity_certificate'] is None and c['status']=='CLOCK_UNDETERMINED'
        return c['status']=='CAPACITY_CERTIFIED' and check_capacity(left,right,edges,c['capacity_certificate'])
    except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False


def _copy_inputs(measurements,left,right):
    if not isinstance(measurements,list) or any(not isinstance(r,dict) for r in measurements) or not isinstance(left,list) or not isinstance(right,list):raise ValueError('Acquisition lists required')
    return [dict(r) for r in measurements],list(left),list(right)

def certify_measured_capacity(model,measurements,left,right,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        r,a,b=_copy_inputs(measurements,left,right)
        return _produce(model,r,a,b,budget)

def verify_measured_capacity(model,measurements,left,right,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        try:r,a,b=_copy_inputs(measurements,left,right)
        except (ValueError,TypeError):return False
        return _verify(model,r,a,b,certificate,budget)

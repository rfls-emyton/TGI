from copy import deepcopy
from tgi.organization_snapshot import snapshot
from tgi.acquisition_monitor_check import verify_acquisition_monitor
from tgi.response_interval_order_check import verify_response_interval_order
from tgi.compact_measured_path import _decimal_count
from tgi.role_work import RoleSearchBudget

def _joint(model,plan,acquisition,source,boundaries,monitor,measurements,order,budget):
    if not verify_acquisition_monitor(model,plan,acquisition,source,boundaries,monitor) or not verify_response_interval_order(acquisition,source,boundaries,measurements,order):
        raise ValueError('Invalid joint acquisition evidence')
    base=dict(policy='joint_temporal_candidates_v1',monitor=deepcopy(monitor),order=deepcopy(order),answer=None)
    if order['status']=='CLOCK_UNDETERMINED':
        return dict(**base,status='CLOCK_UNDETERMINED',nodes=[],edges=[],terminals=[],histogram=[],total=None,stationary=None)
    events=monitor['events'];t=len(events);n=len(plan['contexts']);required=[0]*t
    for left,right in order['precedence']:
        budget.consume();required[right]|=1<<left
    states=[(0,-1,0,0,0)];lookup={states[0]:0};counts=[1];edges=[];cursor=0
    while cursor<len(states):
        budget.consume();mask,last,changes,incompatible,unknown=states[cursor]
        for event in range(t):
            budget.consume()
            if mask&(1<<event) or required[event]&mask!=required[event]:continue
            for candidate in range(n):
                budget.consume();missing=candidate in events[event]['unknown'];mismatch=not missing and candidate not in events[event]['supported']
                key=(mask|(1<<event),candidate,changes+int(last!=-1 and last!=candidate),incompatible+int(mismatch),unknown+int(missing))
                if key not in lookup:lookup[key]=len(states);states.append(key);counts.append(0)
                target=lookup[key];counts[target]+=counts[cursor];edges.append([cursor,target,event,candidate])
        cursor+=1
    terminals=[i for i,key in enumerate(states) if key[0]==(1<<t)-1];bins={}
    for index in terminals:
        budget.consume();key=states[index][2:];value=bins.setdefault(key,[0,[]]);value[0]+=counts[index];value[1].append(index)
    histogram=[dict(changes=k[0],incompatible=k[1],unknown=k[2],count=_decimal_count(v[0]),terminals=v[1]) for k,v in sorted(bins.items())]
    possible=sorted({states[i][1] for i in terminals if states[i][2]==states[i][3]==0});definite=sorted({states[i][1] for i in terminals if states[i][2]==states[i][3]==states[i][4]==0})
    return dict(**base,status='TIME_COMPATIBLE_CANDIDATES',nodes=[dict(mask=s[0],last=s[1],changes=s[2],incompatible=s[3],unknown=s[4],count=_decimal_count(counts[i])) for i,s in enumerate(states)],edges=edges,terminals=terminals,histogram=histogram,total=_decimal_count(sum(counts[i] for i in terminals)),stationary=dict(possible=possible,definite=definite))

def certify_joint_temporal_candidates(model,plan,acquisition,source,boundaries,monitor,measurements,order,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        return _joint(snapshot(model),deepcopy(plan),snapshot(acquisition),source,deepcopy(boundaries),deepcopy(monitor),deepcopy(measurements),deepcopy(order),budget)

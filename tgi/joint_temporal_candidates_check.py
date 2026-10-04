from copy import deepcopy
from tgi.organization_snapshot import snapshot
from tgi.acquisition_monitor_check import verify_acquisition_monitor
from tgi.response_interval_order_check import verify_response_interval_order
from tgi.compact_measured_path import _decimal_count
from tgi.frame_engine import canonical
from tgi.role_work import RoleSearchBudget

def _check(model,plan,acquisition,source,boundaries,monitor,measurements,order,c,budget):
    try:
        if not isinstance(c,dict) or set(c)!={'policy','monitor','order','answer','status','nodes','edges','terminals','histogram','total','stationary'}:return False
        if c['policy']!='joint_temporal_candidates_v1' or c['answer'] is not None or canonical(c['monitor'])!=canonical(monitor) or canonical(c['order'])!=canonical(order):return False
        if not verify_acquisition_monitor(model,plan,acquisition,source,boundaries,monitor) or not verify_response_interval_order(acquisition,source,boundaries,measurements,order):return False
        if order['status']=='CLOCK_UNDETERMINED':
            return c['status']=='CLOCK_UNDETERMINED' and c['nodes']==c['edges']==c['terminals']==c['histogram']==[] and c['total'] is None and c['stationary'] is None
        if c['status']!='TIME_COMPATIBLE_CANDIDATES':return False
        events=monitor['events'];t=len(events);n=len(plan['contexts']);records=[next(r for r in measurements if r['frame']==stop-1) for stop in boundaries[1:]];predecessors=[];local=[]
        for event,row in enumerate(events):
            budget.consume();required=set()
            for other in range(t):
                budget.consume()
                if records[other]['upper']<records[event]['lower']:required.add(other)
            predecessors.append(required);labels=[]
            for candidate in range(n):
                budget.consume();values=[g['value'] for request in plan['requests'] if request['query']==row['request'] for g in request['responses'] if candidate in g['contexts']]
                labels.append((0,0) if event==0 else (0,1) if not values else (int(row['observed'] not in values),0))
            local.append(labels)
        keys=[];lookup={}
        for index,node in enumerate(c['nodes']):
            budget.consume()
            if set(node)!={'mask','last','changes','incompatible','unknown','count'}:return False
            key=tuple(node[k] for k in ('mask','last','changes','incompatible','unknown'))
            if any(type(v) is not int for v in key):return False
            mask,last,changes,incompatible,unknown=key;step=mask.bit_count()
            if not 0<=mask<(1<<t) or not 0<=changes<=max(0,step-1) or not 0<=incompatible<=step or not 0<=unknown<=step or (last!=-1 if step==0 else not 0<=last<n) or key in lookup:return False
            keys.append(key);lookup[key]=index
        if not keys or keys[0]!=(0,-1,0,0,0):return False
        incoming=[[] for _ in keys];edges=[]
        for index,(mask,last,changes,incompatible,unknown) in enumerate(keys):
            budget.consume();present={event for event in range(t) if mask&(1<<event)}
            for event in range(t):
                budget.consume()
                if event in present or not predecessors[event]<=present:continue
                for candidate in range(n):
                    budget.consume();mismatch,missing=local[event][candidate];key=(mask|(1<<event),candidate,changes+int(last!=-1 and last!=candidate),incompatible+mismatch,unknown+missing)
                    if key not in lookup:return False
                    target=lookup[key];edges.append([index,target,event,candidate]);incoming[target].append(index)
        if canonical(c['edges'])!=canonical(edges):return False
        counts=[0]*len(keys);counts[0]=1
        for index in sorted(range(1,len(keys)),key=lambda i:keys[i][0].bit_count()):
            budget.consume();counts[index]=sum(counts[j] for j in incoming[index])
        if any(value==0 for value in counts) or any(node['count']!=_decimal_count(counts[i]) for i,node in enumerate(c['nodes'])):return False
        terminals=[i for i,key in enumerate(keys) if key[0]==(1<<t)-1]
        if canonical(c['terminals'])!=canonical(terminals):return False
        grouped={}
        for index in terminals:
            budget.consume();v=grouped.setdefault(keys[index][2:],[0,[]]);v[0]+=counts[index];v[1].append(index)
        histogram=[dict(changes=k[0],incompatible=k[1],unknown=k[2],count=_decimal_count(v[0]),terminals=v[1]) for k,v in sorted(grouped.items())]
        possible=sorted({keys[i][1] for i in terminals if keys[i][2]==keys[i][3]==0});definite=sorted({keys[i][1] for i in terminals if keys[i][2]==keys[i][3]==keys[i][4]==0})
        return canonical(c['histogram'])==canonical(histogram) and c['total']==_decimal_count(sum(counts[i] for i in terminals)) and canonical(c['stationary'])==canonical(dict(possible=possible,definite=definite))
    except (ValueError,TypeError,KeyError,IndexError,AttributeError,StopIteration):return False

def verify_joint_temporal_candidates(model,plan,acquisition,source,boundaries,monitor,measurements,order,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:return _check(snapshot(model),deepcopy(plan),snapshot(acquisition),source,deepcopy(boundaries),deepcopy(monitor),deepcopy(measurements),deepcopy(order),certificate,budget)
        except (ValueError,TypeError,KeyError,AttributeError):return False

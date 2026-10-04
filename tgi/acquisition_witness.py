"""Source-bound measured-interval evidence; compatibility is not object identity."""
from heapq import heappop,heappush
from .organization_snapshot import snapshot
from .acquisition_snapshot import acquisition_snapshot
from .frame_engine import canonical
from .identity import encode,decode
from .incidence import _endpoint
from .role_work import RoleSearchBudget

_FIELDS={'source','frame','start','stop','clock','lower','upper'}

def _inputs(model,measurements,*,raw=False):
    view=acquisition_snapshot(model) if raw else snapshot(model)
    if not isinstance(measurements,list):raise ValueError('Measurements must be a list')
    records=[];seen=set()
    for r in measurements:
        if not isinstance(r,dict) or set(r)!=_FIELDS:raise ValueError('Invalid measurement schema')
        for key in ('source','clock'):
            if not isinstance(r[key],str) or not r[key].strip():raise ValueError('Measurement authority required')
            encode(r[key])
        if any(type(r[k]) is not int for k in ('frame','start','stop','lower','upper')):raise ValueError('Integer bounds required')
        if r['source'] not in view.episodes:raise ValueError('Unknown source')
        frames=view.episodes[r['source']][0]
        if not 0<=r['frame']<len(frames) or not 0<=r['start']<r['stop']<=len(frames[r['frame']]) or r['lower']>r['upper']:raise ValueError('Invalid measurement bounds')
        key=(r['source'],r['frame'],r['start'],r['stop'])
        if key in seen:raise ValueError('Duplicate occurrence measurement')
        seen.add(key);records.append(dict(r))
    sources=[]
    for sid,(frames,_) in sorted(view.episodes.items()):
        if not view._alive(sid):raise ValueError('Broken source')
        sources.append({'source':sid,'frames':list(map(decode,frames))})
    return view,sorted(records,key=canonical),sources

def _producer_interval_pairs(records):
    """Closed interval sweep; all original cross-source partners survive."""
    clocks={};pairs=[]
    for i,r in enumerate(records):clocks.setdefault(r['clock'],[]).append(i)
    for indices in clocks.values():
        active={};ends=[]
        for i in sorted(indices,key=lambda i:(records[i]['lower'],i)):
            r=records[i];lo=r['lower']
            while ends and ends[0][0]<lo:
                _,j=heappop(ends);sid=records[j]['source'];del active[sid][j]
                if not active[sid]:del active[sid]
            for sid,bucket in active.items():
                if sid==r['source']:continue
                for j in bucket:
                    left,right=sorted((i,j));pairs.append({'left':left,'right':right,'intersection':[lo,min(r['upper'],records[j]['upper'])]})
            active.setdefault(r['source'],{})[i]=None;heappush(ends,(r['upper'],i))
    return sorted(pairs,key=lambda p:(p['left'],p['right']))


def _checker_interval_pairs(records):
    """Independent endpoint-event reconstruction; starts precede equal ends."""
    authorities={};edges=[]
    for index,item in enumerate(records):
        events=authorities.setdefault(item['clock'],[])
        events.extend(((item['lower'],0,index),(item['upper'],1,index)))
    for events in authorities.values():
        live={}
        for instant,kind,index in sorted(events):
            item=records[index];source=item['source']
            if kind:
                live[source].remove(index)
                if not live[source]:del live[source]
                continue
            for owner,others in live.items():
                if owner==source:continue
                for other in others:
                    a,b=(index,other) if index<other else (other,index)
                    edges.append({'left':a,'right':b,'intersection':[max(item['lower'],records[other]['lower']),min(item['upper'],records[other]['upper'])]})
            live.setdefault(source,set()).add(index)
    return sorted(edges,key=lambda e:(e['left'],e['right']))


def _certify_acquisition_witness(model,measurements,*,max_search_steps=None,raw=False):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        view,records,sources=_inputs(model,measurements,raw=raw);occurrences=[];pairs=[]
        for r in records:
            budget.consume();occurrences.append(_endpoint(view,r['source'],(r['frame'],r['start'],r['stop'])))
        budget.consume_many(len(records)*(len(records)-1)//2)
        pairs=_producer_interval_pairs(records)
        return {'policy':'measured_interval_witness_v1','sources':sources,'measurements':records,'occurrences':occurrences,'pairs':pairs,'status':'COMPATIBLE_PAIRS' if pairs else 'NO_COMPATIBLE_PAIR'}

def _verify_acquisition_witness(model,measurements,certificate,*,max_search_steps=None,raw=False):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        try:
            view,records,sources=_inputs(model,measurements,raw=raw)
            if set(certificate)!={'policy','sources','measurements','occurrences','pairs','status'} or certificate['policy']!='measured_interval_witness_v1':return False
            if canonical(certificate['sources'])!=canonical(sources) or canonical(certificate['measurements'])!=canonical(records):return False
            endpoints=[];edges=[]
            for i,r in enumerate(records):
                budget.consume();frames,receipts=view.episodes[r['source']];fi=r['frame'];start=r['start'];stop=r['stop'];origin=receipts[fi].origin;offset=sum(map(len,frames[:fi]))
                endpoints.append({'frame':fi,'start':start,'stop':stop,'event_span':[offset+start,offset+stop],'identities':list(frames[fi][start:stop]),'coordinates':[[origin[0]+p,*origin[1:]] for p in range(start,stop)]})
            budget.consume_many(len(records)*(len(records)-1)//2)
            edges=_checker_interval_pairs(records)
            status='COMPATIBLE_PAIRS' if edges else 'NO_COMPATIBLE_PAIR'
            return canonical(certificate['occurrences'])==canonical(endpoints) and canonical(certificate['pairs'])==canonical(edges) and certificate['status']==status
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False


def certify_acquisition_witness(model,measurements,*,max_search_steps=None):
    return _certify_acquisition_witness(model,measurements,max_search_steps=max_search_steps)


def verify_acquisition_witness(model,measurements,certificate,*,max_search_steps=None):
    return _verify_acquisition_witness(model,measurements,certificate,max_search_steps=max_search_steps)


def certify_raw_acquisition_witness(model,measurements,*,max_search_steps=None):
    return _certify_acquisition_witness(model,measurements,max_search_steps=max_search_steps,raw=True)


def verify_raw_acquisition_witness(model,measurements,certificate,*,max_search_steps=None):
    return _verify_acquisition_witness(model,measurements,certificate,max_search_steps=max_search_steps,raw=True)

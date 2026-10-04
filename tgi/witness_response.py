"""Conditional observed-response consensus over all measured candidate spans."""
from .identity import encode,decode
from .frame_engine import canonical
from .organization_snapshot import snapshot
from .role_work import RoleSearchBudget
from .acquisition_witness import certify_acquisition_witness,verify_acquisition_witness
from .observed_response import certify_observed_response
from .observed_response_check import verify_observed_response

_ROOT={'source','frame','start','stop'}

def _measured_root_index(records,root):
    if not isinstance(root,dict) or set(root)!=_ROOT:raise ValueError('Exact root occurrence required')
    if not isinstance(root['source'],str) or not root['source'].strip():raise ValueError('Root source required')
    encode(root['source'])
    if any(type(root[k]) is not int for k in ('frame','start','stop')) or min(root['frame'],root['start'])<0 or root['stop']<=root['start']:raise ValueError('Invalid root span')
    hits=[i for i,r in enumerate(records) if all(r[k]==root[k] for k in _ROOT)]
    if len(hits)!=1:raise ValueError('Root must be a measured occurrence')
    return hits[0]

def _root_index(records,root,query):
    if not isinstance(query,str) or not query:raise ValueError('Raw query required')
    encode(query)
    return _measured_root_index(records,root)

def certify_witness_response(model,measurements,root,query,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        view=snapshot(model);w=certify_acquisition_witness(view,measurements);i=_root_index(w['measurements'],root,query);neighbors=set()
        for pair in w['pairs']:
            budget.consume()
            if i in (pair['left'],pair['right']):neighbors.add(pair['right'] if pair['left']==i else pair['left'])
        branches=[]
        for j in sorted(neighbors):
            budget.consume();r=w['measurements'][j];context=decode(tuple(w['occurrences'][j]['identities']))
            branches.append({'measurement':dict(r),'response':certify_observed_response(view,[context,query])})
        alternatives=sorted({x for b in branches for x in b['response']['result']['candidates']});complete=bool(branches) and all(b['response']['result']['status']=='OBSERVED_AGREEMENT' for b in branches)
        status='NO_CANDIDATES' if not branches else 'CONFLICT' if len(alternatives)>1 else 'CONDITIONAL_OBSERVED_CONSENSUS' if complete and len(alternatives)==1 else 'UNRESOLVED'
        return {'policy':'witness_observed_response_v1','root':dict(root),'query':query,'witness':w,'branches':branches,'result':{'status':status,'output':alternatives if status=='CONDITIONAL_OBSERVED_CONSENSUS' else [],'alternatives':alternatives}}

def verify_witness_response(model,measurements,root,query,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        try:
            view=snapshot(model)
            if set(certificate)!={'policy','root','query','witness','branches','result'} or certificate['policy']!='witness_observed_response_v1':return False
            if canonical(certificate['root'])!=canonical(root) or certificate['query']!=query:return False
            if not verify_acquisition_witness(view,measurements,certificate['witness']):return False
            records=certificate['witness']['measurements'];i=_root_index(records,root,query);r=records[i];selected=[]
            for j,other in enumerate(records):
                budget.consume()
                if other['source']!=r['source'] and other['clock']==r['clock'] and other['lower']<=r['upper'] and r['lower']<=other['upper']:selected.append(other)
            branches=certificate['branches']
            if not isinstance(branches,list) or len(branches)!=len(selected):return False
            values=set();all_agree=True
            for other,b in zip(selected,branches):
                budget.consume()
                if set(b)!={'measurement','response'} or canonical(b['measurement'])!=canonical(other):return False
                raw=view.episodes[other['source']][0][other['frame']][other['start']:other['stop']]
                if b['response']['prefix']!=[decode(raw),query] or not verify_observed_response(view,b['response']):return False
                values.update(b['response']['result']['candidates']);all_agree &= b['response']['result']['status']=='OBSERVED_AGREEMENT'
            status='UNRESOLVED';output=[]
            if not selected:status='NO_CANDIDATES'
            elif len(values)>1:status='CONFLICT'
            elif all_agree and len(values)==1:status='CONDITIONAL_OBSERVED_CONSENSUS';output=sorted(values)
            return canonical(certificate['result'])==canonical({'status':status,'output':output,'alternatives':sorted(values)})
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

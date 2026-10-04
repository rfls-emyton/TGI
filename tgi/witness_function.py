"""Conditional functional consensus over all measured candidate spans."""
from .identity import encode,decode
from .frame_engine import canonical
from .organization_snapshot import snapshot
from .role_work import RoleSearchBudget
from .acquisition_witness import certify_acquisition_witness,verify_acquisition_witness
from .response_eligibility import certify_response_eligibility
from .functional_transition import certify_functional_eligibility,certify_functional_readout
from .functional_transition_check import verify_functional_eligibility,_verify_functional_readout_contents

from .witness_response import _root_index

def certify_witness_function(model,measurements,root,query,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        view=snapshot(model);w=certify_acquisition_witness(view,measurements);i=_root_index(w['measurements'],root,query);neighbors=set()
        for pair in w['pairs']:
            budget.consume()
            if i in (pair['left'],pair['right']):neighbors.add(pair['right'] if pair['left']==i else pair['left'])
        eligibility=certify_functional_eligibility(view,certify_response_eligibility(view))
        branches=[]
        for j in sorted(neighbors):
            budget.consume();r=w['measurements'][j];context=decode(tuple(w['occurrences'][j]['identities']))
            branches.append({'measurement':dict(r),'response':certify_functional_readout(view,eligibility,[context,query])})
        alternatives=sorted({x for b in branches for x in b['response']['result']['output']});complete=bool(branches) and all(b['response']['result']['status'] in ('OBSERVED_RESPONSE','CONDITIONAL_FUNCTION') for b in branches)
        observed_conflict=any(b['response']['result']['basis']=='observed_conflict' for b in branches)
        status='NO_CANDIDATES' if not branches else 'CONFLICT' if len(alternatives)>1 or observed_conflict else 'CONDITIONAL_FUNCTION_CONSENSUS' if complete and len(alternatives)==1 else 'UNRESOLVED'
        return {'policy':'witness_function_response_v1','root':dict(root),'query':query,'witness':w,'branches':branches,'result':{'status':status,'output':alternatives if status=='CONDITIONAL_FUNCTION_CONSENSUS' else [],'alternatives':alternatives}}

def verify_witness_function(model,measurements,root,query,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        try:
            view=snapshot(model)
            if set(certificate)!={'policy','root','query','witness','branches','result'} or certificate['policy']!='witness_function_response_v1':return False
            if canonical(certificate['root'])!=canonical(root) or certificate['query']!=query:return False
            if not verify_acquisition_witness(view,measurements,certificate['witness']):return False
            records=certificate['witness']['measurements'];i=_root_index(records,root,query);r=records[i];selected=[]
            for j,other in enumerate(records):
                budget.consume()
                if other['source']!=r['source'] and other['clock']==r['clock'] and other['lower']<=r['upper'] and r['lower']<=other['upper']:selected.append(other)
            branches=certificate['branches']
            if not isinstance(branches,list) or len(branches)!=len(selected):return False
            values=set();all_agree=True;conflict=False;verified_eligibility=None
            for other,b in zip(selected,branches):
                budget.consume()
                if set(b)!={'measurement','response'} or canonical(b['measurement'])!=canonical(other):return False
                raw=view.episodes[other['source']][0][other['frame']][other['start']:other['stop']]
                eligibility=b['response']['eligibility']
                if verified_eligibility is None:
                    if not verify_functional_eligibility(view,eligibility):return False
                    verified_eligibility=canonical(eligibility)
                elif canonical(eligibility)!=verified_eligibility:return False
                if b['response']['readout']['prefix']!=[decode(raw),query] or not _verify_functional_readout_contents(view,b['response']):return False
                values.update(b['response']['result']['output']);all_agree &= b['response']['result']['status'] in ('OBSERVED_RESPONSE','CONDITIONAL_FUNCTION')
                conflict |= b['response']['result']['basis']=='observed_conflict'
            status='UNRESOLVED';output=[]
            if not selected:status='NO_CANDIDATES'
            elif len(values)>1 or conflict:status='CONFLICT'
            elif all_agree and len(values)==1:status='CONDITIONAL_FUNCTION_CONSENSUS';output=sorted(values)
            return canonical(certificate['result'])==canonical({'status':status,'output':output,'alternatives':sorted(values)})
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

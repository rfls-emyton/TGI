"""Combine certified observations and inference at the already selected state."""
from .role_response_check import verify_role_response
from .observed_response import certify_observed_response


def certify_evidence_response(model,role,history,inference):
    if not verify_role_response(model,role,history,inference):raise ValueError('Invalid temporal inference')
    temporal=inference['temporal'];rows=[];values=[]
    for response in inference['responses']:
        index=response['window'];window=temporal['windows'][index]
        prefix=temporal['readouts'][window['readout']]['prefix']+[temporal['query']]
        observed=certify_observed_response(model,prefix);actual=observed['result'];predicted=response['resolution']
        value=[];basis='unresolved'
        if actual['status']=='OBSERVED_CONFLICT':basis='observed_conflict'
        elif actual['status']=='OBSERVED_AGREEMENT':
            if predicted['status']=='RESOLVED' and predicted['output']!=actual['output']:basis='evidence_conflict'
            else:value=actual['output'];basis='observed'
        elif predicted['status']=='RESOLVED':value=predicted['output'];basis='inferred'
        rows.append({'window':index,'observed':observed,'basis':basis,'output':value})
        values.append(value)
    available=bool(values) and all(values) and all(value==values[0] for value in values) and not inference['result']['blockers']
    return {'inference':inference,'contexts':rows,'result':{
        'status':'CONDITIONAL_RESPONSE' if available else 'UNRESOLVED','output':values[0] if available else [],
        'conditions':list(inference['result']['conditions'])}}

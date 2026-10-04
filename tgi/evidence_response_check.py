"""Independent reconciliation of direct and inferred temporal evidence."""
from .frame_engine import canonical
from .role_response_check import verify_role_response
from .observed_response_check import verify_observed_response


def verify_evidence_response(model,role,history,certificate):
    try:
        inference=certificate['inference']
        if not verify_role_response(model,role,history,inference):return False
        temporal=inference['temporal'];selected=inference['result']['selected'];rows=certificate['contexts']
        if len(rows)!=len(selected):return False
        values=[];complete=bool(rows)
        for index,response,row in zip(selected,inference['responses'],rows):
            window=temporal['windows'][index]
            prefix=temporal['readouts'][window['readout']]['prefix']+[temporal['query']]
            observed=row['observed']
            if observed['prefix']!=prefix or not verify_observed_response(model,observed):return False
            actual=observed['result'];predicted=response['resolution'];output=[]
            if actual['status']=='OBSERVED_CONFLICT':basis='observed_conflict'
            elif actual['status']=='OBSERVED_AGREEMENT':
                if predicted['status']=='RESOLVED' and actual['output']!=predicted['output']:basis='evidence_conflict'
                else:basis='observed';output=list(actual['output'])
            elif predicted['status']=='RESOLVED':basis='inferred';output=list(predicted['output'])
            else:basis='unresolved'
            expected={'window':index,'observed':observed,'basis':basis,'output':output}
            if canonical(row)!=canonical(expected):return False
            complete=complete and bool(output);values.append(output)
        available=complete and all(v==values[0] for v in values) and not inference['result']['blockers']
        result={'status':'CONDITIONAL_RESPONSE' if available else 'UNRESOLVED','output':values[0] if available else [],
                'conditions':list(inference['result']['conditions'])}
        return set(certificate)=={'inference','contexts','result'} and canonical(certificate['result'])==canonical(result)
    except (TypeError,ValueError,KeyError,IndexError,AttributeError):return False

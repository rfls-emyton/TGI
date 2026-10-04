"""Lossless transport schema for repeated relational evidence; no admission cache."""
from copy import deepcopy
from .role_response_check import verify_role_response

FORMAT='TGI-ROLE-RESPONSE-BUNDLE-V1'


def pack_role_response(model,role,history,certificate):
    if not verify_role_response(model,role,history,certificate):raise ValueError('Invalid response certificate')
    body=deepcopy(certificate)
    for readout in body['temporal']['readouts']:
        del readout['eligibility']
        readout['eligibility_ref']='temporal.eligibility'
    return {'format':FORMAT,'certificate':body}


def unpack_role_response(bundle):
    """Structural decoding only; callers still need the live-evidence verifier."""
    if not isinstance(bundle,dict) or set(bundle)!={'format','certificate'} or bundle['format']!=FORMAT:
        raise ValueError('Unknown bundle schema')
    body=deepcopy(bundle['certificate'])
    if not isinstance(body,dict) or set(body)!={'temporal','responses','result'}:raise ValueError('Invalid body')
    temporal=body['temporal']
    if not isinstance(temporal,dict) or 'eligibility' not in temporal or not isinstance(temporal.get('readouts'),list):
        raise ValueError('Missing shared evidence')
    for readout in temporal['readouts']:
        if (not isinstance(readout,dict) or set(readout)!={'eligibility_ref','prefix','organizations','result'}
            or readout['eligibility_ref']!='temporal.eligibility'):raise ValueError('Invalid shared reference')
        del readout['eligibility_ref']
        readout['eligibility']=temporal['eligibility']
    return body

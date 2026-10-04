"""Decode fixed references independently and verify all live response evidence."""
from copy import deepcopy
from .role_response_check import verify_role_response


def verify_role_bundle(model,role,history,bundle):
    try:
        if set(bundle)!={'format','certificate'} or bundle['format']!='TGI-ROLE-RESPONSE-BUNDLE-V1':return False
        packed=bundle['certificate']
        if set(packed)!={'temporal','responses','result'}:return False
        temporal=packed['temporal'];expanded=[]
        if not isinstance(temporal['readouts'],list):return False
        for row in temporal['readouts']:
            if set(row)!={'eligibility_ref','prefix','organizations','result'} or row['eligibility_ref']!='temporal.eligibility':return False
            expanded.append({'eligibility':deepcopy(temporal['eligibility']),
                             'prefix':deepcopy(row['prefix']),'organizations':deepcopy(row['organizations']),
                             'result':deepcopy(row['result'])})
        restored=deepcopy(packed);restored['temporal']['readouts']=expanded
        return verify_role_response(model,role,history,restored)
    except (TypeError,ValueError,KeyError,IndexError,AttributeError):return False

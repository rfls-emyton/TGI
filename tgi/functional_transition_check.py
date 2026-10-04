"""Independent functional obstruction and readout consensus verification."""
from .organization_snapshot import snapshot
from .response_eligibility_check import verify_response_eligibility
from .response_readout_check import _verify_response_readout_contents
from .frame_engine import canonical


def verify_functional_eligibility(model,certificate):
    try:
        model=snapshot(model)
        if set(certificate)!={'policy','relation','organizations'} or certificate['policy']!='functional_transition_v1':return False
        relation=certificate['relation']
        if not verify_response_eligibility(model,relation):return False
        expected=[]
        for row in relation['organizations']:
            matched=[];obstructed=[]
            for i,check in enumerate(row['checks']):
                # Only complete unique input bindings have supported/opposed states
                # in the independently recomputed relation certificate.
                if check['binding_state'] not in ('supported','opposed'):continue
                matched.append(i)
                if len(set(relation['groups'][i]['outputs']))!=1:obstructed.append(i)
            expected.append({'anchor':row['anchor'],'matched_groups':matched,'multiple_output_groups':obstructed,
                             'eligible':bool(row['eligible'] and len(matched)>0 and len(obstructed)==0)})
        return canonical(certificate['organizations'])==canonical(expected)
    except (KeyError,IndexError,TypeError,ValueError,AttributeError):return False


def _verify_functional_readout_contents(model,certificate):
    """Internal: caller verified this exact eligibility on this snapshot."""
    try:
        if set(certificate)!={'policy','eligibility','readout','result'} or certificate['policy']!='functional_transition_readout_v1':return False
        eligibility=certificate['eligibility'];readout=certificate['readout']
        if canonical(readout['eligibility'])!=canonical(eligibility['relation']) or not _verify_response_readout_contents(model,readout):return False
        admitted={row['anchor'] for row in eligibility['organizations'] if row['eligible']}
        values=[];missing=[]
        for row in readout['organizations']:
            if row['anchor'] in admitted:
                if row['input_identifiable']:
                    value=row['matches'][0]['output']
                    if value is not None:values.append(value)
                elif len(row['matches'])==1:missing.append(row['anchor'])
        alternatives=sorted(set(values));missing=sorted(set(missing));actual=readout['observed']['result']
        status='UNRESOLVED';basis='empirical_function';output=[]
        if actual['status']=='OBSERVED_CONFLICT':basis='observed_conflict'
        elif actual['status']=='OBSERVED_AGREEMENT':status='OBSERVED_RESPONSE';basis='observed';output=actual['output']
        elif len(alternatives)==1 and not missing:status='CONDITIONAL_FUNCTION';output=alternatives
        expected={'status':status,'basis':basis,'output':output,'alternatives':alternatives,'unbound_anchors':missing}
        return canonical(certificate['result'])==canonical(expected)
    except (KeyError,IndexError,TypeError,ValueError,AttributeError):return False


def verify_functional_readout(model,certificate):
    try:
        view=snapshot(model)
        if not verify_functional_eligibility(view,certificate['eligibility']):return False
        return _verify_functional_readout_contents(view,certificate)
    except (KeyError,IndexError,TypeError,ValueError,AttributeError):return False

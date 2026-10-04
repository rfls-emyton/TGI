"""Empirical single-valued transition evidence, separate from relation membership."""
from .organization_snapshot import snapshot
from .response_eligibility_check import verify_response_eligibility
from .response_readout import certify_response_readout


def certify_functional_eligibility(model, relation):
    model=snapshot(model)
    if not verify_response_eligibility(model,relation):
        raise ValueError('Invalid complete relation evidence')
    rows=[]
    for row in relation['organizations']:
        matched=[i for i,c in enumerate(row['checks']) if c['binding_state'] in ('supported','opposed')]
        obstructions=[i for i in matched if len(relation['groups'][i]['outputs'])!=1]
        rows.append({'anchor':row['anchor'],'matched_groups':matched,'multiple_output_groups':obstructions,
                     'eligible':bool(row['eligible'] and matched and not obstructions)})
    return {'policy':'functional_transition_v1','relation':relation,'organizations':rows}


def certify_functional_readout(model, eligibility, prefix):
    from .functional_transition_check import verify_functional_eligibility
    model=snapshot(model)
    if not verify_functional_eligibility(model,eligibility):
        raise ValueError('Invalid functional evidence')
    readout=certify_response_readout(model,eligibility['relation'],prefix)
    allowed={r['anchor'] for r in eligibility['organizations'] if r['eligible']}
    outputs=set();unbound=[]
    for row in readout['organizations']:
        if row['anchor'] not in allowed:continue
        if row['input_identifiable'] and row['matches'][0]['output'] is not None:
            outputs.add(row['matches'][0]['output'])
        elif len(row['matches'])==1 and not row['input_identifiable']:unbound.append(row['anchor'])
    actual=readout['observed']['result']
    if actual['status']=='OBSERVED_CONFLICT':status='UNRESOLVED';output=[];basis='observed_conflict'
    elif actual['status']=='OBSERVED_AGREEMENT':status='OBSERVED_RESPONSE';output=actual['output'];basis='observed'
    elif len(outputs)==1 and not unbound:status='CONDITIONAL_FUNCTION';output=sorted(outputs);basis='empirical_function'
    else:status='UNRESOLVED';output=[];basis='empirical_function'
    return {'policy':'functional_transition_readout_v1','eligibility':eligibility,'readout':readout,
            'result':{'status':status,'basis':basis,'output':output,'alternatives':sorted(outputs),
                      'unbound_anchors':sorted(set(unbound))}}

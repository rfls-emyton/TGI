"""Independent temporal selection, response-proof and consensus verifier."""
from .frame_engine import canonical
from .role_history_check import verify_role_history
from .organization_check import verify_resolution,verify_refusal


def verify_role_response(model,role,history,certificate):
    try:
        temporal=certificate['temporal']
        if not verify_role_history(model,role,history,temporal):return False
        windows=temporal['windows'];frontier=temporal['frontier']
        selected=[];end=-1
        for i in sorted(set(frontier['observed']+frontier['eligible'])):
            if windows[i]['stop']>end:end=windows[i]['stop'];selected=[]
            if windows[i]['stop']==end:selected.append(i)
        blockers=sorted(set(i for i in frontier['excluded']+frontier['unbound'] if windows[i]['stop']>end))
        for i,w in enumerate(windows):
            evidence=temporal['readouts'][w['readout']]['result']
            if w['stop']>end and not evidence['observed_outputs'] and not evidence['eligible_outputs']:
                blockers.append(i)
        blockers=sorted(set(blockers))
        responses=certificate['responses']
        if len(responses)!=len(selected):return False
        outputs=[];complete=bool(selected)
        for i,row in zip(selected,responses):
            if set(row)!={'window','resolution'} or type(row['window']) is not int or row['window']!=i:return False
            prefix=temporal['readouts'][windows[i]['readout']]['prefix']+[temporal['query']]
            r=row['resolution']
            if r['status']=='RESOLVED':
                if set(r)!={'status','output','proofs'} or not verify_resolution(model,prefix,r,terminal_only=True):return False
                outputs.append(r['output'])
            else:
                complete=False
                if not verify_refusal(model,prefix,r,terminal_only=True):return False
        available=complete and bool(outputs) and all(o==outputs[0] for o in outputs) and not blockers
        expected={'status':'CONDITIONAL_RESPONSE' if available else 'UNRESOLVED',
                  'output':outputs[0] if available else [],'selected':selected,'blockers':blockers,
                  'conditions':['observed_or_empirical_role_membership','source_local_latest_state']}
        return set(certificate)=={'temporal','responses','result'} and canonical(certificate['result'])==canonical(expected)
    except (TypeError,ValueError,KeyError,IndexError,AttributeError):return False

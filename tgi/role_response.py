"""Conditional response with state selection preceding response availability."""
from .role_history_check import verify_role_history
from .organization_check import verify_resolution,verify_refusal


def certify_role_response(model,role,history,temporal):
    if not verify_role_history(model,role,history,temporal):raise ValueError('Invalid temporal evidence')
    windows=temporal['windows'];frontier=temporal['frontier']
    candidates=set(frontier['observed'])|set(frontier['eligible'])
    end=max((windows[i]['stop'] for i in candidates),default=-1)
    selected=sorted(i for i in candidates if windows[i]['stop']==end)
    blockers=sorted({i for kind in ('excluded','unbound') for i in frontier[kind] if windows[i]['stop']>end})
    # A new window with no supported role readout is unknown, not irrelevant.
    blockers=sorted(set(blockers)|{i for i,w in enumerate(windows) if w['stop']>end
                    and not temporal['readouts'][w['readout']]['result']['observed_outputs']
                    and not temporal['readouts'][w['readout']]['result']['eligible_outputs']})
    responses=[];outputs=set();all_resolved=bool(selected)
    for i in selected:
        prefix=temporal['readouts'][windows[i]['readout']]['prefix']+[temporal['query']]
        result=model.resolve(prefix,terminal_only=True)
        resolved=result['status']=='RESOLVED'
        if resolved:
            result={k:result[k] for k in ('status','output','proofs')}
            valid=verify_resolution(model,prefix,result,terminal_only=True)
            outputs.add(tuple(result['output']))
        else:valid=verify_refusal(model,prefix,result,terminal_only=True)
        if not valid:raise ValueError('Uncertified response evidence')
        all_resolved &= resolved
        responses.append({'window':i,'resolution':result})
    available=all_resolved and len(outputs)==1 and not blockers
    return {'temporal':temporal,'responses':responses,
            'result':{'status':'CONDITIONAL_RESPONSE' if available else 'UNRESOLVED',
                      'output':list(next(iter(outputs))) if available else [],'selected':selected,'blockers':blockers,
                      'conditions':['observed_or_empirical_role_membership','source_local_latest_state']}}

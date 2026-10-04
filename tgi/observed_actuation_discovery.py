"""All original available raw commands; effects must come from measured laws."""
from copy import deepcopy
from .acquisition_snapshot import acquisition_snapshot
from .acquisition_witness import certify_raw_acquisition_witness
from .observed_joint_state import certify_observed_joint_state
from .measured_context_laws import certify_measured_context_laws
from .identity import decode
from .role_work import RoleSearchBudget


def catalogue_records(view,measurements,budget):
    expected={(s,i) for s,(frames,_) in view.episodes.items() for i in range(len(frames))};seen=set();records=[]
    if not expected:raise ValueError('Original nonempty raw actuation catalogue required')
    for row in measurements:
        budget.consume();key=(row['source'],row['frame'])
        if key in seen or key not in expected:raise ValueError('Unique complete catalogue coverage required')
        ids=view.episodes[key[0]][0][key[1]]
        if row['start']!=0 or row['stop']!=len(ids) or not ids:raise ValueError('Whole nonempty command frame required')
        seen.add(key);records.append({'source':key[0],'frame':key[1],'action':decode(ids),'measurement':deepcopy(row)})
    if seen!=expected:raise ValueError('Every original raw catalogue frame required')
    return sorted(records,key=lambda r:(r['source'],r['frame']))


def certify_observed_actuation_discovery(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,catalogue,catalogue_measurements,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume();groups,measurements,observed_groups,observed_measurements,catalogue_measurements=deepcopy((groups,measurements,observed_groups,observed_measurements,catalogue_measurements));view=acquisition_snapshot(catalogue);state=certify_observed_joint_state(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group);witness=certify_raw_acquisition_witness(view,catalogue_measurements);records=catalogue_records(view,catalogue_measurements,budget);actions=sorted({r['action'] for r in records});ready=state['result']['status']=='JOINT_STATE_READY';fresh=ready;laws=[];requests=[];predicted=[]
        for record in records:
            for point in state['points']:
                budget.consume();a=record['measurement'];b=point['measurement'];fresh &= a['clock']==b['clock'] and a['lower']>b['upper']
        if fresh:
            for action in actions:
                unresolved=[];output={}
                for port in state['ports']:
                    budget.consume();context={p:state['state'][p] for p in state['ports'] if p!=port};c=certify_measured_context_laws(model,groups,measurements,port,state['state'][port],action,context);laws.append({'port':port,'action':action,'certificate':c})
                    if c['result']['status']=='MEASURED_CONTEXT_LAW_RESOLVED':output[port]=c['result']['output'][0]
                    else:unresolved.append(port)
                if unresolved:requests.append({'action':action,'before':deepcopy(state['state']),'unresolved_ports':unresolved})
                else:predicted.append({'action':action,'state':output})
        status='ACTUATION_STATE_UNRESOLVED' if not ready else 'ACTUATION_CATALOGUE_NOT_CURRENT' if not fresh else 'ACTUATION_EXPERIENCE_REQUESTS_READY' if requests else 'AVAILABLE_ACTIONS_SUPPORTED'
        return {'policy':'observed_actuation_discovery_v1','state_certificate':state,'catalogue_witness':witness,'catalogue_records':records,'available_actions':actions,'laws':laws,'requests':requests,'result':{'status':status,'catalogue_current':bool(fresh),'supported_actions':[x['action'] for x in predicted],'predicted_states':predicted,'request_count':len(requests)}}

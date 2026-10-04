"""Independent raw catalogue, full joint state and every action law checker."""
from copy import deepcopy
from .acquisition_snapshot import acquisition_snapshot
from .acquisition_witness import verify_raw_acquisition_witness
from .observed_joint_state_check import verify_observed_joint_state
from .measured_context_laws_check import verify_measured_context_laws
from .identity import decode
from .frame_engine import canonical
from .role_work import RoleSearchBudget


def verify_observed_actuation_discovery(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,catalogue,catalogue_measurements,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            c=deepcopy(certificate)
            if set(c)!={'policy','state_certificate','catalogue_witness','catalogue_records','available_actions','laws','requests','result'} or c['policy']!='observed_actuation_discovery_v1':return False
            state=c['state_certificate']
            if not verify_observed_joint_state(model,groups,measurements,observation,observed_groups,observed_measurements,anchor_group,state):return False
            view=acquisition_snapshot(catalogue)
            if not verify_raw_acquisition_witness(view,catalogue_measurements,c['catalogue_witness']):return False
            expected={(s,i) for s,(frames,_) in view.episodes.items() for i in range(len(frames))};covered=set();records=[]
            if not expected:return False
            for row in catalogue_measurements:
                budget.consume();key=(row['source'],row['frame'])
                if key not in expected or key in covered:return False
                ids=view.episodes[key[0]][0][key[1]]
                if not ids or row['start']!=0 or row['stop']!=len(ids):return False
                covered.add(key);records.append({'source':key[0],'frame':key[1],'action':decode(ids),'measurement':deepcopy(row)})
            if covered!=expected:return False
            records.sort(key=lambda r:(r['source'],r['frame']));actions=sorted({r['action'] for r in records})
            if canonical(c['catalogue_records'])!=canonical(records) or c['available_actions']!=actions:return False
            ready=state['result']['status']=='JOINT_STATE_READY';fresh=ready
            for record in records:
                for point in state['points']:
                    budget.consume();a=record['measurement'];b=point['measurement'];fresh &= a['clock']==b['clock'] and a['lower']>b['upper']
            if len(c['laws'])!=(len(actions)*len(state['ports']) if fresh else 0):return False
            requests=[];predicted=[];cursor=0
            if fresh:
                for action in actions:
                    output={};unresolved=[]
                    for port in state['ports']:
                        budget.consume();item=c['laws'][cursor];cursor+=1
                        if set(item)!={'port','action','certificate'} or item['port']!=port or item['action']!=action:return False
                        context={p:state['state'][p] for p in state['ports'] if p!=port};law=item['certificate']
                        if not verify_measured_context_laws(model,groups,measurements,port,state['state'][port],action,context,law):return False
                        if law['result']['status']=='MEASURED_CONTEXT_LAW_RESOLVED':output[port]=law['result']['output'][0]
                        else:unresolved.append(port)
                    if unresolved:requests.append({'action':action,'before':deepcopy(state['state']),'unresolved_ports':unresolved})
                    else:predicted.append({'action':action,'state':output})
            status='ACTUATION_STATE_UNRESOLVED' if not ready else 'ACTUATION_CATALOGUE_NOT_CURRENT' if not fresh else 'ACTUATION_EXPERIENCE_REQUESTS_READY' if requests else 'AVAILABLE_ACTIONS_SUPPORTED';result={'status':status,'catalogue_current':bool(fresh),'supported_actions':[x['action'] for x in predicted],'predicted_states':predicted,'request_count':len(requests)}
            return canonical(c['requests'])==canonical(requests) and canonical(c['result'])==canonical(result)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

"""Independent lineage knowledge coverage, raw opposition and polarity verifier."""
from copy import deepcopy
from .lineage_state_check import verify_lineage_state
from .intervention_composition_check import verify_intervention_composition
from .intervention_scope import decode_scope
from .organization_snapshot import snapshot
from .observed_response_check import verify_observed_response
from .frame_engine import canonical
from .role_work import RoleSearchBudget


def verify_lineage_knowledge(old,bridge,new,root_port,anchor,actions,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            c=deepcopy(certificate)
            if set(c)!={'policy','state','composition','observations','result'} or c['policy']!='native_lineage_knowledge_v1':return False
            state=c['state']
            if not verify_lineage_state(old,bridge,new,root_port,anchor,actions,state):return False
            status=state['result']['status'];output=[];polarities=[];bases=[];composition=c['composition']
            if status!='OBSERVED_STATE_READY':
                if composition is not None or c['observations']!=[]:return False
            else:
                if not verify_intervention_composition(*new,state['port'],state['result']['seed'][0],actions,composition):return False
                shared=composition['substrate'];local=decode_scope(snapshot(new[0]),shared['source_scope'],shared['inventory'])
                if not isinstance(c['observations'],list) or len(c['observations'])!=len(composition['steps']):return False
                contradicted=False
                for step,direct in zip(composition['steps'],c['observations']):
                    budget.consume()
                    for _ in local.episodes:budget.consume()
                    if direct['prefix']!=[step['before'],step['action']] or not verify_observed_response(local,direct):return False
                    resolved=step['result']['status']=='ROLE_STRUCTURAL_RESOLUTION';answer=step['result']['output'][0] if resolved else None;observed=direct['result']
                    if observed['status']=='OBSERVED_CONFLICT' or (resolved and observed['status']=='OBSERVED_AGREEMENT' and observed['output']!=[answer]):contradicted=True
                    polarities.append(int(step['before']!=answer) if resolved else None)
                    bases.append('OBSERVED_AND_GEOMETRIC' if resolved and observed['output']==[answer] else 'GEOMETRIC_GENERALIZATION' if resolved and observed['status']=='NO_OBSERVATION' else 'UNRESOLVED')
                status='OBSERVATION_CONTRADICTION' if contradicted else 'GEOMETRIC_KNOWLEDGE_SUPPORTED' if composition['result']['status']=='COMPOSED_ROLE_RESOLUTION' else 'INCOMPLETE_GEOMETRY'
                if status=='GEOMETRIC_KNOWLEDGE_SUPPORTED':output=composition['result']['output']
            result={'status':status,'output':output,'visible_change_polarity':polarities,'basis':bases}
            return canonical(c['result'])==canonical(result)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

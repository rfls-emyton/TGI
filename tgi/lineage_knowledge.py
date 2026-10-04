"""Knowledge decisions from native lineage, geometric operators and raw opposition."""
from .lineage_state import certify_lineage_state
from .intervention_composition import certify_intervention_composition
from .intervention_scope import decode_scope
from .organization_snapshot import snapshot
from .observed_response import certify_observed_response
from .role_work import RoleSearchBudget


def certify_lineage_knowledge(old,bridge,new,root_port,anchor,actions,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume();state=certify_lineage_state(old,bridge,new,root_port,anchor,actions)
        composition=None;observations=[];polarities=[];bases=[]
        status=state['result']['status'];output=[]
        if status=='OBSERVED_STATE_READY':
            composition=certify_intervention_composition(*new,state['port'],state['result']['seed'][0],actions)
            shared=composition['substrate'];local=decode_scope(snapshot(new[0]),shared['source_scope'],shared['inventory']);conflict=False
            for step in composition['steps']:
                budget.consume()
                for _ in local.episodes:budget.consume()
                direct=certify_observed_response(local,[step['before'],step['action']]);observations.append(direct)
                resolved=step['result']['status']=='ROLE_STRUCTURAL_RESOLUTION';after=step['result']['output'][0] if resolved else None
                conflict |= direct['result']['status']=='OBSERVED_CONFLICT' or (resolved and direct['result']['status']=='OBSERVED_AGREEMENT' and direct['result']['output']!=[after])
                polarities.append(int(step['before']!=after) if resolved else None)
                bases.append('OBSERVED_AND_GEOMETRIC' if resolved and direct['result']['output']==[after] else 'GEOMETRIC_GENERALIZATION' if resolved and direct['result']['status']=='NO_OBSERVATION' else 'UNRESOLVED')
            status='OBSERVATION_CONTRADICTION' if conflict else 'GEOMETRIC_KNOWLEDGE_SUPPORTED' if composition['result']['status']=='COMPOSED_ROLE_RESOLUTION' else 'INCOMPLETE_GEOMETRY'
            if status=='GEOMETRIC_KNOWLEDGE_SUPPORTED':output=composition['result']['output']
        return {'policy':'native_lineage_knowledge_v1','state':state,'composition':composition,'observations':observations,'result':{'status':status,'output':output,'visible_change_polarity':polarities,'basis':bases}}

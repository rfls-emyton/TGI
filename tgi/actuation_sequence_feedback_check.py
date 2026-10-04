"""Original choice, actual available-command records and coherent sequence outcome."""
from .actuation_goal_frontier_check import verify_actuation_goal_frontier
from .measured_actuation_transition_check import verify_measured_actuation_transition
from .observed_actuation_discovery_check import verify_observed_actuation_discovery
from .observed_actuation_runtime import raw
from .joint_goal_traversal_check import _initial_owners
from .frame_engine import canonical
from .role_work import RoleSearchBudget

def same_state_context(a,b,budget):
    budget.consume()
    return len(a)>=7 and len(b)>=7 and all(canonical(raw(a[i]))==canonical(raw(b[i])) for i in (0,3)) and canonical([a[1],a[2],a[4],a[5],a[6]])==canonical([b[1],b[2],b[4],b[5],b[6]])

def verify_actuation_sequence_feedback(origin,goal,frontier,selection_index,records,current,current_plan,certificate,*,max_depth=None,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        try:
            budget.consume()
            if len(origin)!=9 or len(current)!=9 or not verify_actuation_goal_frontier(*origin,goal,frontier,max_depth=max_depth):raise ValueError('Original verified available-command frontier required')
            if type(selection_index) is not int or not 0<=selection_index<len(frontier['choices']):raise ValueError('Original exact choice index required')
            if not verify_observed_actuation_discovery(*current,current_plan):raise ValueError('Verified current actual state/capability plan required')
            choice=frontier['choices'][selection_index];previous=origin;steps=[];status='SELECTED_SEQUENCE_PENDING';terminal=False
            if not choice['actions']:status='GOAL_ALREADY_ACTUALLY_OBSERVED';terminal=True
            for position,record in enumerate(records):
                budget.consume()
                if terminal or position>=len(choice['actions']) or type(record) is not dict or set(record)!={'context','after','certificate'}:raise ValueError('No extra, malformed or post-terminal record')
                context=record['context'];after=record['after'];c=record['certificate']
                if len(context)!=15 or not same_state_context(context,previous,budget) or not verify_measured_actuation_transition(*context,after,c) or not c['result']['experience_admitted']:raise ValueError('Complete linked actual transition required')
                edge=frontier['edges'][choice['edges'][position]];before=frontier['nodes'][edge['source']]['state']
                if canonical(context[9]['state_certificate']['state'])!=canonical(before) or c['selected_action']!=choice['actions'][position] or c['selected_action']!=edge['action']:raise ValueError('Original selected before state and command required')
                expected=frontier['nodes'][edge['successor']]['state'] if edge['supported'] else None;actual=c['result']['actual_state'];route='UNRESOLVED' if expected is None else 'MATCHED' if actual==expected else 'CONTRADICTED'
                if expected is None:status='FRONTIER_EXPERIENCE_ACTUALLY_VERIFIED';terminal=True
                elif route!='MATCHED' or c['result']['prediction_outcome']!='MATCHED' or canonical(c['predicted_state'])!=canonical(expected):status='ACTUAL_EVIDENCE_REPLAN_REQUIRED';terminal=True
                elif position+1==len(choice['actions']):status='SUPPORTED_GOAL_ACTUALLY_VERIFIED' if choice['kind']=='SUPPORTED_GOAL' else 'SUPPORTED_PREFIX_ACTUALLY_VERIFIED';terminal=True
                else:status='SUPPORTED_PREFIX_PROGRESS_VERIFIED'
                steps.append({'position':position,'edge':choice['edges'][position],'selected_action':c['selected_action'],'projected_after':expected,'current_prediction':c['predicted_state'],'actual_state':actual,'route_outcome':route,'current_prediction_outcome':c['result']['prediction_outcome'],'actual_lineage_routes':_initial_owners(c['next_state'],budget),'transition':c})
                h=c['history'];anchor=h.get('acquired_group_indices',list(range(len(context[1]),len(context[1])+len(context[12]))))[context[14]];previous=(after,h['groups'],h['measurements'],after,h['groups'],h['measurements'],anchor)
            if not same_state_context(current,previous,budget):raise ValueError('Original complete last actual successor required')
            state=current_plan['state_certificate'];observed=state['result']['status']=='JOINT_STATE_READY' and all(state['state'][p]==v for p,v in goal.items());verified=terminal and status in ('GOAL_ALREADY_ACTUALLY_OBSERVED','SUPPORTED_GOAL_ACTUALLY_VERIFIED','SUPPORTED_PREFIX_ACTUALLY_VERIFIED')
            result={'status':status,'consumed_steps':len(steps),'remaining_steps':len(choice['actions'])-len(steps),'terminal':terminal,'selected_supported_path_actually_verified':verified,'actual_goal_observed':bool(observed),'catalogue_current':current_plan['result']['catalogue_current']}
            expected_certificate={'policy':'actuation_sequence_feedback_v1','frontier':frontier,'selection_index':selection_index,'current_discovery':current_plan,'steps':steps,'result':result}
            return canonical(certificate)==canonical(expected_certificate)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

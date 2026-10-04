"""Measured prefix feedback over every originally admitted geometric sequence."""
from copy import deepcopy
from .identity import decode
from .organization_snapshot import snapshot
from .intervention_sequence_experiment import certify_sequence_observation
from .role_work import RoleSearchBudget


def certify_sequence_prefix_observation(model,groups,measurements,seed,max_depth,plan,acquisition,acquired_groups,observed_measurements,sources,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume();model=snapshot(model);acquisition=snapshot(acquisition);groups,measurements,plan,acquired_groups,observed_measurements,sources=deepcopy((groups,measurements,plan,acquired_groups,observed_measurements,sources))
        base=certify_sequence_observation(model,groups,measurements,seed,max_depth,plan,acquisition,acquired_groups,observed_measurements,sources)
        actions=[decode(acquisition.episodes[s][0][1]) for s in sources];lookup={(r['source'],r['frame']):r for r in observed_measurements};last=lookup[sources[-1],1];latest=True
        for source in acquisition.episodes:
            budget.consume();other=lookup[source,1];latest &= other['clock']==last['clock'] and (other['upper']<=last['lower'] or (other['lower'],other['upper'])==(last['lower'],last['upper']))
        comparisons=[];classes=set();next_actions=set();trace=base['result']['trace'];count=len(actions);planned=False
        for index,row in enumerate(plan['rows']):
            budget.consume()
            if row['actions'] not in plan['result']['sequences'] or row['actions'][:count]!=actions:continue
            planned=True;outcomes=[];members=set()
            for outcome,item in enumerate(row['outcomes']):
                budget.consume()
                if item['trace'][:count]==trace:outcomes.append(outcome);members.update(item['classes'])
            classes.update(members)
            if members and count<len(row['actions']):next_actions.add(row['actions'][count])
            comparisons.append({'row':index,'outcomes':outcomes,'classes':sorted(members)})
        status='INCOMPLETE_PREFIX_OBSERVATION' if not base['result']['ordered'] else 'STALE_PREFIX_OBSERVATION' if not latest else 'UNPLANNED_PREFIX' if not planned else 'UNMODELED_PREFIX' if not classes else 'CLASS_PROFILE_IDENTIFIED' if len(classes)==1 else 'PREFIX_CONTINUATION_READY' if next_actions else 'CLASS_PROFILE_AMBIGUOUS'
        valid=status in ('CLASS_PROFILE_IDENTIFIED','PREFIX_CONTINUATION_READY','CLASS_PROFILE_AMBIGUOUS');candidates=sorted(classes) if valid else [] if status=='UNMODELED_PREFIX' else list(range(len(plan['classes'])))
        result={'status':status,'trace':trace,'candidate_classes':candidates,'candidate_blocks':[plan['classes'][i] for i in candidates],'next_actions':sorted(next_actions) if status=='PREFIX_CONTINUATION_READY' else []}
        return {'policy':'native_sequence_prefix_observation_v1','base':base,'actions':actions,'latest_selected_action':bool(latest),'comparisons':comparisons,'result':result}


def certify_sequence_continuation(model,groups,measurements,seed,max_depth,plan,previous,previous_groups,previous_measurements,previous_sources,prior,acquisition,acquired_groups,observed_measurements,sources,*,max_search_steps=None):
    from .sequence_prefix_feedback_check import verify_sequence_prefix_observation
    from .frame_engine import canonical
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume();model,previous,acquisition=snapshot(model),snapshot(previous),snapshot(acquisition);groups,measurements,plan,previous_groups,previous_measurements,previous_sources,prior,acquired_groups,observed_measurements,sources=deepcopy((groups,measurements,plan,previous_groups,previous_measurements,previous_sources,prior,acquired_groups,observed_measurements,sources))
        if not verify_sequence_prefix_observation(model,groups,measurements,seed,max_depth,plan,previous,previous_groups,previous_measurements,previous_sources,prior) or prior['result']['status']!='PREFIX_CONTINUATION_READY':raise ValueError('Verified continuation-ready original prefix required')
        if type(sources) is not list or len(sources)!=len(previous_sources)+1 or sources[:-1]!=list(previous_sources) or sources[-1] in previous_sources:raise ValueError('Original ordered sources plus one new source required')
        if canonical(acquired_groups[:len(previous_groups)])!=canonical(previous_groups):raise ValueError('Complete original acquisition group prefix required')
        lookup={(x['source'],x['frame']):x for x in observed_measurements}
        for source,episode in previous.episodes.items():
            budget.consume()
            if source not in acquisition.episodes or acquisition.episodes[source]!=episode:raise ValueError('Every original acquired episode must be retained exactly')
        for row in previous_measurements:
            budget.consume()
            if lookup.get((row['source'],row['frame']))!=row:raise ValueError('Every original acquired measurement must be retained exactly')
        feedback=certify_sequence_prefix_observation(model,groups,measurements,seed,max_depth,plan,acquisition,acquired_groups,observed_measurements,sources);new=sources[-1];old=previous_sources[-1];assignment={x['source']:x['port'] for group in acquired_groups for x in group};last={(x['source'],x['frame']):x for x in previous_measurements}[old,2];before=lookup[new,0];act=lookup[new,1];action=decode(acquisition.episodes[new][0][1]);uninterrupted=True
        for source,(frames,_) in acquisition.episodes.items():
            budget.consume();point=lookup[source,1];shared=(point['clock'],point['lower'],point['upper'])==(act['clock'],act['lower'],act['upper']) and decode(frames[1])==action
            uninterrupted &= point['clock']==last['clock'] and (shared or point['upper']<=last['upper'] or point['lower']>before['upper'])
        guard={'same_interface':assignment[new]==assignment[old],'same_before':decode(acquisition.episodes[new][0][0])==decode(previous.episodes[old][0][2]),'later_same_clock':before['clock']==last['clock'] and last['upper']<before['lower'],'uninterrupted':bool(uninterrupted),'new_prefix_ordered':feedback['base']['result']['ordered'],'new_prefix_latest':feedback['latest_selected_action'],'requested_action':action in prior['result']['next_actions'],'candidate_subset':set(feedback['result']['candidate_classes'])<=set(prior['result']['candidate_classes'])}
        ordered=all(guard[k] for k in ('same_interface','same_before','later_same_clock','uninterrupted','new_prefix_ordered','new_prefix_latest'));admitted=bool(ordered and guard['requested_action'] and guard['candidate_subset']);status='INCOMPLETE_CONTINUATION' if not ordered else 'UNPLANNED_CONTINUATION' if not guard['requested_action'] else 'INCONSISTENT_PREFIX_CLASS_BINDING' if not guard['candidate_subset'] else 'CONTINUATION_OBSERVED';candidates=feedback['result']['candidate_classes'] if admitted else prior['result']['candidate_classes']
        result={'status':status,'observation_admitted':admitted,'feedback_status':feedback['result']['status'] if admitted else None,'candidate_classes':candidates,'candidate_blocks':[plan['classes'][i] for i in candidates],'next_actions':feedback['result']['next_actions'] if admitted else []}
        return {'policy':'native_sequence_continuation_v1','prior':prior,'feedback':feedback,'sources':sources,'guard':guard,'result':result}

"""Independent native prefix, complete outcome coverage and continuation check."""
from copy import deepcopy
from .identity import decode
from .organization_snapshot import snapshot
from .intervention_sequence_experiment_check import verify_sequence_observation
from .frame_engine import canonical
from .role_work import RoleSearchBudget


def verify_sequence_prefix_observation(model,groups,measurements,seed,max_depth,plan,acquisition,acquired_groups,observed_measurements,sources,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            model=snapshot(model);acquisition=snapshot(acquisition);groups,measurements,plan,acquired_groups,observed_measurements,sources,c=deepcopy((groups,measurements,plan,acquired_groups,observed_measurements,sources,certificate))
            if set(c)!={'policy','base','actions','latest_selected_action','comparisons','result'} or c['policy']!='native_sequence_prefix_observation_v1':return False
            if not verify_sequence_observation(model,groups,measurements,seed,max_depth,plan,acquisition,acquired_groups,observed_measurements,sources,c['base']):return False
            actions=[]
            for source in sources:
                budget.consume();actions.append(decode(acquisition.episodes[source][0][1]))
            if type(c['actions']) is not list or canonical(c['actions'])!=canonical(actions):return False
            bounds={(x['source'],x['frame']):x for x in observed_measurements};end=bounds[sources[-1],1];latest=True
            for source in acquisition.episodes:
                budget.consume();point=bounds[source,1]
                if point['clock']!=end['clock'] or not (point['upper']<=end['lower'] or (point['lower']==end['lower'] and point['upper']==end['upper'])):latest=False
            if type(c['latest_selected_action']) is not bool or c['latest_selected_action']!=latest:return False
            comparisons=[];survivors=set();following=set();matched=False;trace=c['base']['result']['trace'];length=len(actions)
            for index,row in enumerate(plan['rows']):
                budget.consume()
                if row['actions'] not in plan['result']['sequences'] or row['actions'][:length]!=actions:continue
                matched=True;indices=[];members=set()
                for position,outcome in enumerate(row['outcomes']):
                    budget.consume()
                    if outcome['trace'][:length]==trace:indices.append(position);members.update(outcome['classes'])
                comparisons.append({'row':index,'outcomes':indices,'classes':sorted(members)});survivors.update(members)
                if members and length<len(row['actions']):following.add(row['actions'][length])
            if type(c['comparisons']) is not list or canonical(c['comparisons'])!=canonical(comparisons):return False
            if not c['base']['result']['ordered']:status='INCOMPLETE_PREFIX_OBSERVATION'
            elif not latest:status='STALE_PREFIX_OBSERVATION'
            elif not matched:status='UNPLANNED_PREFIX'
            elif not survivors:status='UNMODELED_PREFIX'
            elif len(survivors)==1:status='CLASS_PROFILE_IDENTIFIED'
            elif following:status='PREFIX_CONTINUATION_READY'
            else:status='CLASS_PROFILE_AMBIGUOUS'
            valid=status in ('CLASS_PROFILE_IDENTIFIED','PREFIX_CONTINUATION_READY','CLASS_PROFILE_AMBIGUOUS');candidates=sorted(survivors) if valid else [] if status=='UNMODELED_PREFIX' else list(range(len(plan['classes'])))
            result={'status':status,'trace':trace,'candidate_classes':candidates,'candidate_blocks':[plan['classes'][i] for i in candidates],'next_actions':sorted(following) if status=='PREFIX_CONTINUATION_READY' else []}
            return canonical(c['result'])==canonical(result)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False


def verify_sequence_continuation(model,groups,measurements,seed,max_depth,plan,previous,previous_groups,previous_measurements,previous_sources,prior,acquisition,acquired_groups,observed_measurements,sources,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            model,previous,acquisition=snapshot(model),snapshot(previous),snapshot(acquisition);groups,measurements,plan,previous_groups,previous_measurements,previous_sources,prior,acquired_groups,observed_measurements,sources,c=deepcopy((groups,measurements,plan,previous_groups,previous_measurements,previous_sources,prior,acquired_groups,observed_measurements,sources,certificate))
            if set(c)!={'policy','prior','feedback','sources','guard','result'} or c['policy']!='native_sequence_continuation_v1' or canonical(c['prior'])!=canonical(prior) or canonical(c['sources'])!=canonical(sources):return False
            if not verify_sequence_prefix_observation(model,groups,measurements,seed,max_depth,plan,previous,previous_groups,previous_measurements,previous_sources,prior) or prior['result']['status']!='PREFIX_CONTINUATION_READY':return False
            if type(sources) is not list or len(sources)!=len(previous_sources)+1 or sources[:-1]!=list(previous_sources) or sources[-1] in previous_sources:return False
            if canonical(acquired_groups[:len(previous_groups)])!=canonical(previous_groups):return False
            bounds={(x['source'],x['frame']):x for x in observed_measurements}
            for source,episode in previous.episodes.items():
                budget.consume()
                if source not in acquisition.episodes or acquisition.episodes[source]!=episode:return False
            for row in previous_measurements:
                budget.consume()
                if bounds.get((row['source'],row['frame']))!=row:return False
            f=c['feedback']
            if not verify_sequence_prefix_observation(model,groups,measurements,seed,max_depth,plan,acquisition,acquired_groups,observed_measurements,sources,f):return False
            old=previous_sources[-1];new=sources[-1];ports={x['source']:x['port'] for group in acquired_groups for x in group};end=next(x for x in previous_measurements if x['source']==old and x['frame']==2);begin=bounds[new,0];act=bounds[new,1];action=decode(acquisition.episodes[new][0][1]);uninterrupted=True
            for source,(frames,_) in acquisition.episodes.items():
                budget.consume();point=bounds[source,1];alias=point['clock']==act['clock'] and point['lower']==act['lower'] and point['upper']==act['upper'] and decode(frames[1])==action
                if point['clock']!=end['clock'] or not (alias or point['upper']<=end['upper'] or point['lower']>begin['upper']):uninterrupted=False
            guard={'same_interface':ports[new]==ports[old],'same_before':decode(acquisition.episodes[new][0][0])==decode(previous.episodes[old][0][2]),'later_same_clock':begin['clock']==end['clock'] and end['upper']<begin['lower'],'uninterrupted':uninterrupted,'new_prefix_ordered':f['base']['result']['ordered'],'new_prefix_latest':f['latest_selected_action'],'requested_action':action in prior['result']['next_actions'],'candidate_subset':set(f['result']['candidate_classes'])<=set(prior['result']['candidate_classes'])}
            if canonical(c['guard'])!=canonical(guard):return False
            ordered=all(guard[k] for k in ('same_interface','same_before','later_same_clock','uninterrupted','new_prefix_ordered','new_prefix_latest'));admitted=bool(ordered and guard['requested_action'] and guard['candidate_subset']);status='INCOMPLETE_CONTINUATION' if not ordered else 'UNPLANNED_CONTINUATION' if not guard['requested_action'] else 'INCONSISTENT_PREFIX_CLASS_BINDING' if not guard['candidate_subset'] else 'CONTINUATION_OBSERVED';candidates=f['result']['candidate_classes'] if admitted else prior['result']['candidate_classes']
            result={'status':status,'observation_admitted':admitted,'feedback_status':f['result']['status'] if admitted else None,'candidate_classes':candidates,'candidate_blocks':[plan['classes'][i] for i in candidates],'next_actions':f['result']['next_actions'] if admitted else []}
            return canonical(c['result'])==canonical(result)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError,StopIteration):return False

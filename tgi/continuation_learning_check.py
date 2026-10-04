"""Independent whole raw history, crystal phase and actual-state renewal checker."""
from copy import deepcopy
from .organization import RawOrganization
from .organization_snapshot import snapshot
from .identity import decode
from .frame_engine import canonical
from .sequence_prefix_feedback_check import verify_sequence_continuation
from .organization_inventory_check import verify_organization_inventory
from .compact_complete_role_core_check import verify_compact_complete_role_core as verify_complete_role_core
from .complete_role_core import projected_domain
from .intervention_sequence_experiment_check import verify_intervention_sequence_experiments
from .role_work import RoleSearchBudget


def verify_continuation_learning(model,groups,measurements,seed,max_depth,plan,previous,previous_groups,previous_measurements,previous_sources,prior,acquisition,acquired_groups,observed_measurements,sources,continuation,after,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            c=certificate;model,previous,acquisition=snapshot(model),snapshot(previous),snapshot(acquisition)
            if set(c)!={'policy','continuation','history','core','renewed_seed','renewed','result'} or c['policy']!='native_continuation_learning_v1' or canonical(c['continuation'])!=canonical(continuation):return False
            if not verify_sequence_continuation(model,groups,measurements,seed,max_depth,plan,previous,previous_groups,previous_measurements,previous_sources,prior,acquisition,acquired_groups,observed_measurements,sources,continuation):return False
            admitted=continuation['result']['observation_admitted']
            if not admitted:
                return after is None and all(c[k] is None for k in ('history','core','renewed_seed','renewed')) and canonical(c['result'])==canonical({'status':'CONTINUATION_NOT_ADMITTED','experience_admitted':False,'renewed_status':None})
            actual=snapshot(after);raw=RawOrganization();mapping=[];episodes=[];gs=[];ms=[]
            for domain,original,layouts,rows in [('learned',model,groups,measurements),('acquired',acquisition,acquired_groups,observed_measurements)]:
                names={}
                for ordinal,(source,(frames,_)) in enumerate(original.episodes.items()):
                    name=canonical([domain,ordinal]);budget.consume_many(sum(map(len,frames))+len(source)+len(name)+1);names[source]=name;text=list(map(decode,frames));raw.observe(name,text);mapping.append({'domain':domain,'ordinal':ordinal,'original_source':source,'source':name});episodes.append({'source':name,'frames':text})
                for group in layouts:
                    budget.consume_many(len(group)+1);gs.append([{'port':x['port'],'source':names[x['source']]} for x in group])
                for row in rows:budget.consume();ms.append({**deepcopy(row),'source':names[row['source']]})
            expected={'policy':'joint_history_ordinal_v1','source_map':mapping,'episodes':episodes,'groups':gs,'measurements':ms}
            if canonical(c['history'])!=canonical(expected) or actual.episodes!=raw.episodes:return False
            for name in ('atoms','bonds','origins'):
                if getattr(actual.frames.view(),name)!=getattr(raw.frames.view(),name):return False
            if not verify_organization_inventory(actual) or not verify_complete_role_core(actual,gs,ms,c['core']):return False
            newseed=decode(acquisition.episodes[sources[-1]][0][2])
            if c['renewed_seed']!=newseed:return False
            if c['core']['ports']:
                if c['renewed'].get('policy')=='native_scoped_sequence_experiment_v1':
                    if canonical(c['renewed'].get('scope'))!=canonical(c['core']):return False
                    if not verify_intervention_sequence_experiments(actual,gs,ms,newseed,max_depth,c['renewed']):return False
                else:
                    local,localgroups,localms,_=projected_domain(actual,gs,ms,c['core']['ports'])
                    if not verify_intervention_sequence_experiments(local,localgroups,localms,newseed,max_depth,c['renewed']):return False
                status=c['renewed']['result']['status']
            else:
                if c['renewed'] is not None:return False
                status='NO_COMPLETE_ROLE_CORE'
            return canonical(c['result'])==canonical({'status':'CONTINUATION_EXPERIENCE_LEARNED','experience_admitted':True,'renewed_status':status})
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

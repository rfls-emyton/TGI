"""Independent complete observed-state, operation and native lineage check."""
from .identity import decode,encode
from .frame_engine import canonical
from .organization_snapshot import snapshot
from .intervention_continuity_check import verify_intervention_continuity
from .role_work import RoleSearchBudget


def verify_lineage_state(old,bridge,new,root_port,anchor,actions,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            if not isinstance(anchor,dict) or set(anchor)!={'source','frame'} or not isinstance(anchor['source'],str) or type(anchor['frame']) is not int or anchor['frame'] not in (0,2):return False
            if not isinstance(actions,(list,tuple)) or not actions or any(not isinstance(a,str) or not a for a in actions):return False
            for action in actions:encode(action)
            c=certificate
            if set(c)!={'policy','root_port','anchor','actions','lineage','port','states','inventory','result'} or c['policy']!='lineage_observed_state_v1' or c['root_port']!=root_port or canonical(c['anchor'])!=canonical(anchor) or canonical(c['actions'])!=canonical(list(actions)):return False
            if not verify_intervention_continuity(old,bridge,new,root_port,c['lineage']):return False
            view=snapshot(new[0]);groups=new[1];lookup={(r['source'],r['frame']):r for r in new[2]}
            assignment={s['source']:s['port'] for group in groups for s in group}
            port=assignment[anchor['source']]
            def endpoint(source,frame):
                frames,receipts=view.episodes[source];origin=receipts[frame].origin;n=len(frames[frame]);offset=sum(len(f) for f in frames[:frame])
                return {'frame':frame,'start':0,'stop':n,'event_span':[offset,offset+n],'identities':list(frames[frame]),'coordinates':[list((origin[0]+i,)+origin[1:]) for i in range(n)]}
            states=[];by_action={}
            for group in groups:
                for spec in group:
                    budget.consume()
                    if spec['port']!=port:continue
                    s=spec['source'];frames=view.episodes[s][0]
                    states.extend({'source':s,'occurrence':endpoint(s,i),'measurement':lookup[s,i]} for i in (0,2))
                    action=decode(frames[1]);by_action.setdefault(action,[]).append({'source':s,'action':endpoint(s,1),'before':endpoint(s,0),'after':endpoint(s,2),'visible_change':int(frames[0]!=frames[2])})
            inventory=[{'action':a,'occurrences':by_action[a]} for a in sorted(by_action)]
            anchor_bounds=lookup[anchor['source'],anchor['frame']];latest=True
            for s in states:
                if (s['source'],s['occurrence']['frame'])==(anchor['source'],anchor['frame']):continue
                b=s['measurement'];latest &= b['clock']==anchor_bounds['clock'] and b['upper']<anchor_bounds['lower']
            missing=[a for a in actions if a not in by_action];status='OBSERVED_STATE_READY'
            if c['lineage']['result']['status']!='CONDITIONAL_ROLE_CONTINUITY':status='LINEAGE_UNRESOLVED'
            elif port not in c['lineage']['result']['output_ports']:status='UNRELATED_ANCHOR'
            elif not latest:status='STATE_UNRESOLVED'
            elif missing:status='ACTION_UNOBSERVED'
            result={'status':status,'latest_in_scope':bool(latest),'unobserved_actions':missing,'seed':[decode(view.episodes[anchor['source']][0][anchor['frame']])] if status=='OBSERVED_STATE_READY' else []}
            return c['port']==port and canonical(c['states'])==canonical(states) and canonical(c['inventory'])==canonical(inventory) and canonical(c['result'])==canonical(result)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

"""Bind a continuing endogenous role to an original latest observed state."""
from copy import deepcopy
from .identity import decode,encode
from .incidence import _endpoint
from .organization_snapshot import snapshot
from .intervention_continuity import certify_intervention_continuity
from .role_work import RoleSearchBudget


def certify_lineage_state(old,bridge,new,root_port,anchor,actions,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        if not isinstance(anchor,dict) or set(anchor)!={'source','frame'} or not isinstance(anchor['source'],str) or type(anchor['frame']) is not int or anchor['frame'] not in (0,2):raise ValueError('Original before/after anchor required')
        if not isinstance(actions,(list,tuple)) or not actions or any(not isinstance(a,str) or not a for a in actions):raise ValueError('Nonempty raw action sequence required')
        for a in actions:encode(a)
        lineage=certify_intervention_continuity(old,bridge,new,root_port)
        view=snapshot(new[0]);groups=deepcopy(new[1]);measurements=deepcopy(new[2])
        port=next((s['port'] for g in groups for s in g if s['source']==anchor['source']),None)
        if port is None:raise ValueError('Anchor source absent from acquisition')
        lookup={(r['source'],r['frame']):r for r in measurements};states=[];inventory={}
        for group in groups:
            for spec in group:
                budget.consume()
                if spec['port']!=port:continue
                source=spec['source'];frames=view.episodes[source][0]
                for frame in (0,2):
                    states.append({'source':source,'occurrence':_endpoint(view,source,(frame,0,len(frames[frame]))),'measurement':lookup[source,frame]})
                action=decode(frames[1]);inventory.setdefault(action,[]).append({'source':source,'action':_endpoint(view,source,(1,0,len(frames[1]))),'before':_endpoint(view,source,(0,0,len(frames[0]))),'after':_endpoint(view,source,(2,0,len(frames[2]))),'visible_change':int(frames[0]!=frames[2])})
        point=next(s for s in states if s['source']==anchor['source'] and s['occurrence']['frame']==anchor['frame'])
        bounds=point['measurement'];latest=all(s is point or (s['measurement']['clock']==bounds['clock'] and s['measurement']['upper']<bounds['lower']) for s in states)
        missing=[a for a in actions if a not in inventory]
        status='OBSERVED_STATE_READY'
        if lineage['result']['status']!='CONDITIONAL_ROLE_CONTINUITY':status='LINEAGE_UNRESOLVED'
        elif port not in lineage['result']['output_ports']:status='UNRELATED_ANCHOR'
        elif not latest:status='STATE_UNRESOLVED'
        elif missing:status='ACTION_UNOBSERVED'
        rows=[{'action':a,'occurrences':inventory[a]} for a in sorted(inventory)]
        return {'policy':'lineage_observed_state_v1','root_port':root_port,'anchor':deepcopy(anchor),'actions':list(actions),'lineage':lineage,'port':port,'states':states,'inventory':rows,'result':{'status':status,'latest_in_scope':latest,'unobserved_actions':missing,'seed':[decode(view.episodes[anchor['source']][0][anchor['frame']])] if status=='OBSERVED_STATE_READY' else []}}

"""Complete conditional role continuity through an observed interface bridge."""
from copy import deepcopy
from itertools import product
from .organization_snapshot import snapshot
from .intervention_roles import certify_intervention_roles
from .compact_measured_path import _read_count,_decimal_count
from .role_work import RoleSearchBudget


def certify_intervention_continuity(old,bridge,new,root_port,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume();epochs=[]
        for acquisition in (old,bridge,new):
            if acquisition is None:epochs.append(None);continue
            if not isinstance(acquisition,(tuple,list)) or len(acquisition)!=3:raise ValueError('Acquisition triple required')
            model,groups,measurements=acquisition
            epochs.append(certify_intervention_roles(snapshot(model),deepcopy(groups),deepcopy(measurements)))
        left,middle,right=epochs
        if left is None or right is None or root_port not in left['ports']:raise ValueError('Original root required')
        root=left['ports'].index(root_port);bridge_root=middle['ports'].index(root_port) if middle and root_port in middle['ports'] else None
        histogram={}
        for lp,bp,rp in product(left['partitions'],middle['partitions'] if middle else [None],right['partitions']):
            budget.consume();old_block=next(tuple(b) for b in lp['blocks'] if root in b)
            bridge_block=next(tuple(b) for b in bp['blocks'] if bridge_root in b) if bridge_root is not None else None
            matched=[];is_open=bridge_block is None;bridge_names={middle['ports'][i] for i in bridge_block} if bridge_block is not None else set()
            for block in rp['blocks']:
                budget.consume();names={right['ports'][i] for i in block};unseen=middle is None or not names<=set(middle['ports'])
                if bridge_block is None or names & bridge_names or unseen:matched.append(tuple(block))
                is_open |= unseen
            if not matched:is_open=True
            eligible=next(c['eligible'] for c in left['role_candidates'] if c['ports']==list(old_block))
            eligible &= bridge_block is not None and next(c['eligible'] for c in middle['role_candidates'] if c['ports']==list(bridge_block))
            eligible &= all({right['ports'][i] for i in block}<=bridge_names for block in matched)
            eligible &= all(next(c['eligible'] for c in right['role_candidates'] if c['ports']==list(block)) for block in matched)
            key=(old_block,bridge_block,tuple(matched),bool(is_open),bool(eligible))
            count=_read_count(lp['count'])*_read_count(rp['count'])*(_read_count(bp['count']) if bp else 1);histogram[key]=histogram.get(key,0)+count
        rows=[{'old_block':list(ob),'bridge_block':list(bb) if bb is not None else None,'targets':[list(b) for b in targets],'open':is_open,'eligible':eligible,'count':_decimal_count(count)} for (ob,bb,targets,is_open,eligible),count in sorted(histogram.items(),key=lambda item:repr(item[0]))]
        possible=sorted({tuple(b) for row in rows for b in row['targets']});certain=set(map(tuple,rows[0]['targets'])) if rows else set()
        for row in rows:certain &= set(map(tuple,row['targets']))
        ready=bool(rows) and len(possible)==1 and all(not row['open'] and row['eligible'] and len(row['targets'])==1 for row in rows)
        return {'policy':'bridged_intervention_role_continuity_v1','root_port':root_port,'epochs':epochs,'outcomes':rows,'total_completions':_decimal_count(sum(histogram.values())),
                'result':{'status':'CONDITIONAL_ROLE_CONTINUITY' if ready else 'UNRESOLVED','possible_targets':[list(b) for b in possible],'common_possible_targets':[list(b) for b in sorted(certain)],'certain_targets':[list(b) for b in possible] if ready else [],'output_ports':[right['ports'][i] for i in possible[0]] if ready else []}}

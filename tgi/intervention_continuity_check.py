"""Independent complete epoch/bridge role-lineage outcome verification."""
from copy import deepcopy
from .frame_engine import canonical
from .organization_snapshot import snapshot
from .intervention_roles_check import verify_intervention_roles
from .compact_measured_path import _read_count,_decimal_count
from .role_work import RoleSearchBudget


def verify_intervention_continuity(old,bridge,new,root_port,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            c=deepcopy(certificate)
            if set(c)!={'policy','root_port','epochs','outcomes','total_completions','result'} or c['policy']!='bridged_intervention_role_continuity_v1' or c['root_port']!=root_port:return False
            if not isinstance(c['epochs'],list) or len(c['epochs'])!=3:return False
            epochs=c['epochs']
            for raw,role in zip((old,bridge,new),epochs):
                if raw is None:
                    if role is not None:return False
                elif not isinstance(raw,(tuple,list)) or len(raw)!=3 or not verify_intervention_roles(snapshot(raw[0]),deepcopy(raw[1]),deepcopy(raw[2]),role):return False
            left,middle,right=epochs
            if left is None or right is None or root_port not in left['ports']:return False
            li=left['ports'].index(root_port);bi=middle['ports'].index(root_port) if middle and root_port in middle['ports'] else None
            counts={}
            for lp in left['partitions']:
                ob=next(tuple(b) for b in lp['blocks'] if li in b)
                for bp in middle['partitions'] if middle else [None]:
                    bb=next(tuple(b) for b in bp['blocks'] if bi in b) if bi is not None else None
                    same={middle['ports'][i] for i in bb} if bb is not None else set();seen=set(middle['ports']) if middle else set()
                    for rp in right['partitions']:
                        budget.consume();targets=[];open_domain=bb is None;compatible=True
                        for block in rp['blocks']:
                            budget.consume();names=set(right['ports'][i] for i in block)
                            unobserved=bool(names-seen)
                            if bb is None or not names.isdisjoint(same) or unobserved:
                                targets.append(tuple(block));compatible &= names.issubset(same)
                            open_domain |= unobserved
                        if not targets:open_domain=True
                        support=any(row['ports']==list(ob) and row['eligible'] for row in left['role_candidates'])
                        support &= bb is not None and any(row['ports']==list(bb) and row['eligible'] for row in middle['role_candidates'])
                        support &= compatible and all(any(row['ports']==list(t) and row['eligible'] for row in right['role_candidates']) for t in targets)
                        key=(ob,bb,tuple(targets),bool(open_domain),bool(support));weight=_read_count(lp['count'])*_read_count(rp['count'])
                        if bp is not None:weight*=_read_count(bp['count'])
                        counts[key]=counts.get(key,0)+weight
            expected=[]
            for (ob,bb,targets,is_open,support),weight in sorted(counts.items(),key=lambda item:repr(item[0])):
                expected.append({'old_block':list(ob),'bridge_block':list(bb) if bb is not None else None,'targets':[list(b) for b in targets],'open':is_open,'eligible':support,'count':_decimal_count(weight)})
            possible=set();certain=None
            for row in expected:
                candidates=set(map(tuple,row['targets']));possible|=candidates;certain=candidates if certain is None else certain & candidates
            all_targets=sorted(possible);ready=bool(expected) and len(all_targets)==1 and all(row['eligible'] and not row['open'] and len(row['targets'])==1 for row in expected)
            result={'status':'CONDITIONAL_ROLE_CONTINUITY' if ready else 'UNRESOLVED','possible_targets':[list(b) for b in all_targets],'common_possible_targets':[list(b) for b in sorted(certain or set())],'certain_targets':[list(b) for b in all_targets] if ready else [],'output_ports':[right['ports'][i] for i in all_targets[0]] if ready else []}
            return canonical(c['outcomes'])==canonical(expected) and c['total_completions']==_decimal_count(sum(counts.values())) and canonical(c['result'])==canonical(result)
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

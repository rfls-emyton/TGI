"""Native visible intervention-role partitions; no world-object labels."""
from copy import deepcopy
from .identity import decode,encode
from .organization import OMEGA_CRIT
from .organization_snapshot import snapshot
from .acquisition_witness import certify_acquisition_witness
from .compact_measured_path import _decimal_count
from .role_work import RoleSearchBudget


def _cells(acquisition,groups,measurements):
    view=snapshot(acquisition);witness=certify_acquisition_witness(view,measurements)
    if not isinstance(groups,list) or not groups:raise ValueError('Groups required')
    lookup={(r['source'],r['frame']):r for r in measurements}
    if len(lookup)!=len(measurements):raise ValueError('One full-frame measurement required')
    expected={(s,i) for s,(frames,_) in view.episodes.items() for i in range(len(frames))}
    if set(lookup)!=expected:raise ValueError('Complete measurement coverage required')
    for (s,i),r in lookup.items():
        if r['start']!=0 or r['stop']!=len(view.episodes[s][0][i]):raise ValueError('Whole-frame measurements required')
    ports=[];used=set();records=[];diversity={};windows=[]
    for group in groups:
        if not isinstance(group,list) or not group:raise ValueError('Nonempty view group required')
        cells={};actions=set();action_bounds=set();context_windows={};before_values={}
        for spec in group:
            if not isinstance(spec,dict) or set(spec)!={'port','source'}:raise ValueError('Invalid view layout')
            port=spec['port'];source=spec['source']
            encode(port)
            if not isinstance(port,str) or not port or port in cells or source in used or source not in view.episodes:raise ValueError('Duplicate or missing view source')
            frames=view.episodes[source][0]
            if len(frames)!=3:raise ValueError('Exactly before/action/after frames required')
            used.add(source);actions.add(decode(frames[1]))
            if port not in ports:ports.append(port);diversity[port]=set()
            before,action,after=(lookup[source,i] for i in range(3))
            action_bounds.add((action['clock'],action['lower'],action['upper']))
            context_windows[port]=(before['clock'],before['lower'],after['upper'])
            before_values[port]=frames[0]
            certain=len({before['clock'],action['clock'],after['clock']})==1 and before['upper']<=action['lower'] and action['upper']<=after['lower']
            value=int(frames[0]!=frames[2]) if certain else None
            cells[port]=value
            
        if len(actions)!=1 or len(action_bounds)!=1:raise ValueError('One consistent measured action per group required')
        windows.append(next(iter(action_bounds)))
        records.append({'action':next(iter(actions)),'cells':cells,'windows':context_windows,'before':before_values})
    if used!=set(view.episodes):raise ValueError('Complete source coverage required')
    for index,r in enumerate(records):
        for port,value in list(r['cells'].items()):
            clock,lower,upper=r['windows'][port]
            if any(other_clock!=clock or not (other_upper<lower or other_lower>upper) for j,(other_clock,other_lower,other_upper) in enumerate(windows) if j!=index):value=None
            r['cells'][port]=value
            if value==1:diversity[port].add(r['before'][port])
    rows=[{'action':r['action'],'cells':[r['cells'].get(p) for p in ports]} for r in records]
    return witness,ports,rows,[len(diversity[p]) for p in ports]


def certify_intervention_roles(acquisition,groups,measurements,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume();groups,measurements=deepcopy(groups),deepcopy(measurements)
        witness,ports,rows,diversity=_cells(snapshot(acquisition),groups,measurements)
        family={ (tuple(range(len(ports))),):1 }
        for row in rows:
            next_family={};unknown=[i for i,x in enumerate(row['cells']) if x is None]
            for bits in range(1<<len(unknown)):
                budget.consume();values=list(row['cells'])
                for k,i in enumerate(unknown):values[i]=(bits>>k)&1
                for partition,count in family.items():
                    budget.consume();blocks=[]
                    for block in partition:
                        for value in (0,1):
                            part=tuple(i for i in block if values[i]==value)
                            if part:blocks.append(part)
                    key=tuple(sorted(blocks));next_family[key]=next_family.get(key,0)+count
            family=next_family
        partitions=[{'blocks':[list(b) for b in p],'count':_decimal_count(c)} for p,c in sorted(family.items())]
        known=all(x is not None for r in rows for x in r['cells'])
        candidates=[]
        for block in sorted({b for partition in family for b in partition}):
            omega=min(diversity[i] for i in block)
            candidates.append({'ports':list(block),'omega':omega,'eligible':omega>=OMEGA_CRIT and all(row['cells'][i] is not None for row in rows for i in block) and all(block in partition for partition in family)})
        return {'policy':'visible_intervention_roles_v1','groups':groups,'witness':witness,'ports':ports,
                'rows':rows,'changed_before_diversity':diversity,'partitions':partitions,
                'completions':_decimal_count(sum(family.values())),'role_candidates':candidates,
                'status':'DETERMINED_VISIBLE_ROLES' if known else 'UNCERTAIN_ATTRIBUTION'}

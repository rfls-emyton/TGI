"""Independent source/cell/complete-partition verifier for visible roles."""
from copy import deepcopy
from .identity import decode,encode
from .organization import OMEGA_CRIT
from .organization_snapshot import snapshot
from .acquisition_witness import verify_acquisition_witness
from .compact_measured_path import _decimal_count
from .frame_engine import canonical
from .role_work import RoleSearchBudget


def verify_intervention_roles(acquisition,groups,measurements,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        budget.consume()
        try:
            fields={'policy','groups','witness','ports','rows','changed_before_diversity','partitions','completions','role_candidates','status'}
            c=certificate
            if set(c)!=fields or c['policy']!='visible_intervention_roles_v1' or canonical(c['groups'])!=canonical(groups):return False
            view=snapshot(acquisition);groups=deepcopy(groups);measurements=deepcopy(measurements)
            if not verify_acquisition_witness(view,measurements,c['witness']):return False
            if not isinstance(groups,list) or not groups:return False
            measured={};expected={(s,i) for s,(frames,_) in view.episodes.items() for i in range(len(frames))}
            for r in measurements:
                k=(r['source'],r['frame'])
                if k in measured or r['start']!=0 or r['stop']!=len(view.episodes[k[0]][0][k[1]]):return False
                measured[k]=r
            if set(measured)!=expected:return False
            ports=[];used=set();cells=[];raw_inputs={};operations=[]
            for group in groups:
                if not isinstance(group,list) or not group:return False
                observed={};action_values=[];op_bounds=set();windows={};before_values={}
                for spec in group:
                    if not isinstance(spec,dict) or set(spec)!={'port','source'}:return False
                    p,s=spec['port'],spec['source']
                    encode(p)
                    if not isinstance(p,str) or not p or p in observed or s in used or s not in view.episodes:return False
                    frames=view.episodes[s][0]
                    if len(frames)!=3:return False
                    used.add(s)
                    if p not in ports:ports.append(p);raw_inputs[p]=set()
                    action_values.append(decode(frames[1]));bounds=[measured[s,i] for i in range(3)]
                    op_bounds.add((bounds[1]['clock'],bounds[1]['lower'],bounds[1]['upper']))
                    windows[p]=(bounds[0]['clock'],bounds[0]['lower'],bounds[2]['upper']);before_values[p]=frames[0]
                    value=None
                    if all(r['clock']==bounds[0]['clock'] for r in bounds) and bounds[0]['upper']<=bounds[1]['lower'] and bounds[1]['upper']<=bounds[2]['lower']:
                        value=0 if frames[0]==frames[2] else 1
                    observed[p]=value
                    
                if len(set(action_values))!=1 or len(op_bounds)!=1:return False
                operations.append(next(iter(op_bounds)));cells.append((action_values[0],observed,windows,before_values))
            if used!=set(view.episodes) or canonical(ports)!=canonical(c['ports']):return False
            for index,(_,values,windows,before_values) in enumerate(cells):
                for port in values:
                    clock,begin,end=windows[port]
                    for other,(op_clock,op_begin,op_end) in enumerate(operations):
                        if other==index:continue
                        if op_clock!=clock or not (op_end<begin or end<op_begin):values[port]=None;break
                    if values[port]==1:raw_inputs[port].add(before_values[port])
            rows=[{'action':a,'cells':[values.get(p) for p in ports]} for a,values,_,_ in cells]
            diversity=[len(raw_inputs[p]) for p in ports]
            if canonical(rows)!=canonical(c['rows']) or canonical(diversity)!=canonical(c['changed_before_diversity']):return False
            # Independent row refinements enumerate all admissible bit columns;
            # merge only partitions with identical equivalence membership.
            states={tuple([tuple(range(len(ports)))]):1}
            for row in rows:
                options=[()]
                for value in row['cells']:
                    choices=(0,1) if value is None else (value,)
                    new=[]
                    for prefix in options:
                        for choice in choices:budget.consume();new.append(prefix+(choice,))
                    options=new
                result={}
                for values in options:
                    for old,count in states.items():
                        budget.consume();parts=[]
                        for block in old:
                            bins={}
                            for i in block:bins.setdefault(values[i],[]).append(i)
                            parts.extend(tuple(v) for v in bins.values())
                        partition=tuple(sorted(parts));result[partition]=result.get(partition,0)+count
                states=result
            expected_partitions=[{'blocks':[list(b) for b in p],'count':_decimal_count(count)} for p,count in sorted(states.items())]
            certain=all(v is not None for r in rows for v in r['cells'])
            blocks=sorted({b for state in states for b in state});candidates=[]
            for block in blocks:
                omega=min(diversity[i] for i in block)
                candidates.append({'ports':list(block),'omega':omega,'eligible':omega>=OMEGA_CRIT and all(r['cells'][i] is not None for r in rows for i in block) and all(block in state for state in states)})
            return canonical(expected_partitions)==canonical(c['partitions']) and canonical(candidates)==canonical(c['role_candidates']) and c['completions']==_decimal_count(sum(states.values())) and c['status']==('DETERMINED_VISIBLE_ROLES' if certain else 'UNCERTAIN_ATTRIBUTION')
        except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

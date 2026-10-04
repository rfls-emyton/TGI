"""Conditional chronological feasibility of one explicit occurrence path."""
from .acquisition_witness import certify_acquisition_witness,verify_acquisition_witness
from .measured_occurrence_path import _inputs
from .organization_snapshot import snapshot
from .role_work import RoleSearchBudget
from .frame_engine import canonical

_ASSUMPTIONS=['source_frame_order_is_chronological','joins_tested_as_possible_coincidences']


def _path_inputs(view,w,root,path,budget):
    if not isinstance(path,list) or not path or any(not isinstance(s,str) for s in path):raise ValueError('Explicit nonempty source path required')
    sources,ids=_inputs(view,w,root,len(path))
    if path[0]!=root['source'] or any(s not in sources for s in path):raise ValueError('Path outside measured root scope')
    occurrences=[[ids[s,0],ids[s,1]] for s in path];joins=[]
    for a,b in zip(path,path[1:]):
        budget.consume();i,j=ids[a,1],ids[b,0];ra,rb=w['measurements'][i],w['measurements'][j]
        if a==b or ra['clock']!=rb['clock'] or ra['upper']<rb['lower'] or rb['upper']<ra['lower'] or view.episodes[a][0][1]!=view.episodes[b][0][0]:raise ValueError('Not a compatible occurrence path')
        joins.append([i,j])
    return occurrences,joins,sorted({i for pair in occurrences for i in pair})


def certify_path_temporal_feasibility(m,measurements,root,path,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        view=snapshot(m);w=certify_acquisition_witness(view,measurements);occurrences,joins,indices=_path_inputs(view,w,root,path,budget)
        edges=sorted({tuple(p) for p in occurrences}|{(a,b) for a,b in joins}|{(b,a) for a,b in joins});records=w['measurements'];clocks=sorted({records[i]['clock'] for i in indices});bounds=[];violations=[]
        if len(clocks)==1:
            lower={i:records[i]['lower'] for i in indices}
            while True:
                budget.consume();changed=False
                for a,b in edges:
                    budget.consume()
                    if lower[a]>lower[b]:lower[b]=lower[a];changed=True
                if not changed:break
            bounds=[dict(occurrence=i,required_lower=lower[i],upper=records[i]['upper']) for i in indices];violations=[r['occurrence'] for r in bounds if r['required_lower']>r['upper']]
        status='CLOCK_UNDETERMINED' if len(clocks)!=1 else 'TEMPORALLY_INFEASIBLE' if violations else 'TEMPORALLY_FEASIBLE'
        return dict(policy='explicit_path_temporal_feasibility_v1',assumptions=list(_ASSUMPTIONS),root=dict(root),path=list(path),witness=w,occurrences=occurrences,joins=joins,constraints=[list(e) for e in edges],clocks=clocks,bounds=bounds,violations=violations,status=status)


def verify_path_temporal_feasibility(m,measurements,root,path,c,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        try:
            view=snapshot(m)
            if set(c)!={'policy','assumptions','root','path','witness','occurrences','joins','constraints','clocks','bounds','violations','status'} or c['policy']!='explicit_path_temporal_feasibility_v1' or c['assumptions']!=_ASSUMPTIONS or canonical(c['root'])!=canonical(root) or canonical(c['path'])!=canonical(path):return False
            w=c['witness']
            if not verify_acquisition_witness(view,measurements,w):return False
            occurrences,joins,indices=_path_inputs(view,w,root,path,budget)
            edges=set()
            for pair in occurrences:edges.add(tuple(pair))
            for a,b in joins:edges.add((a,b));edges.add((b,a))
            if canonical(c['occurrences'])!=canonical(occurrences) or canonical(c['joins'])!=canonical(joins) or canonical(c['constraints'])!=canonical([list(e) for e in sorted(edges)]):return False
            records=w['measurements'];clocks=sorted({records[i]['clock'] for i in indices});bounds=[];violations=[]
            if len(clocks)==1:
                predecessors={i:[] for i in indices}
                for a,b in edges:predecessors[b].append(a)
                for target in indices:
                    seen={target};pending=[target]
                    while pending:
                        budget.consume();node=pending.pop()
                        for a in predecessors[node]:
                            budget.consume()
                            if a not in seen:seen.add(a);pending.append(a)
                    required=max(records[i]['lower'] for i in seen);bounds.append(dict(occurrence=target,required_lower=required,upper=records[target]['upper']))
                    if required>records[target]['upper']:violations.append(target)
            status='CLOCK_UNDETERMINED' if len(clocks)!=1 else 'TEMPORALLY_INFEASIBLE' if violations else 'TEMPORALLY_FEASIBLE'
            return canonical(c['clocks'])==canonical(clocks) and canonical(c['bounds'])==canonical(bounds) and canonical(c['violations'])==canonical(violations) and c['status']==status
        except (KeyError,IndexError,TypeError,ValueError,AttributeError):return False

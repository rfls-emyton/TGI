"""Complete finite occurrence paths under explicit acquisition compatibility.

Local steps are observed two-frame sources. Cross-source compatibility never
asserts physical identity or semantic transitivity. Hop count is caller scope.
"""
from tgi.acquisition_witness import certify_acquisition_witness,verify_acquisition_witness
from tgi.organization_snapshot import snapshot
from tgi.role_work import RoleSearchBudget
from tgi.frame_engine import canonical
from tgi.identity import decode


def _inputs(view,w,root,hops):
    if type(hops) is not int or hops<1:raise ValueError('Positive exact hop count required')
    if not isinstance(root,dict) or set(root)!={'source','frame','start','stop'}:raise ValueError('Root occurrence required')
    if any(type(root[k]) is not int for k in ('frame','start','stop')):raise ValueError('Integer root span required')
    sources=sorted(s for s,(f,_) in view.episodes.items() if len(f)==2);indices={}
    for s in sources:
        for fi in (0,1):
            found=[i for i,r in enumerate(w['measurements']) if (r['source'],r['frame'],r['start'],r['stop'])==(s,fi,0,len(view.episodes[s][0][fi]))]
            if len(found)!=1:raise ValueError('Incomplete full-frame measurement coverage')
            indices[s,fi]=found[0]
    if root['source'] not in sources or root['frame']!=0 or root['start']!=0 or root['stop']!=len(view.episodes[root['source']][0][0]):raise ValueError('Root must be a full first frame')
    return sources,indices


def certify_measured_occurrence_paths(m,measurements,root,hops,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        view=snapshot(m);w=certify_acquisition_witness(view,measurements);sources,ids=_inputs(view,w,root,hops)
        compatible={frozenset((p['left'],p['right'])) for p in w['pairs']};adj={s:[] for s in sources}
        for a in sources:
          for b in sources:
            budget.consume()
            if view.episodes[a][0][1]==view.episodes[b][0][0] and frozenset((ids[a,1],ids[b,0])) in compatible:adj[a].append(b)
        pending=[(root['source'],)]
        for _ in range(hops-1):
            following=[]
            for path in pending:
                for target in adj[path[-1]]:budget.consume();following.append(path+(target,))
            pending=following
            if not pending:break
        paths=[]
        for p in sorted(pending):
            budget.consume();paths.append(dict(sources=list(p),occurrences=[[ids[s,0],ids[s,1]] for s in p],joins=[[ids[a,1],ids[b,0]] for a,b in zip(p,p[1:])],terminal=decode(view.episodes[p[-1]][0][1])))
        return dict(policy='measured_occurrence_paths_v1',root=dict(root),hops=hops,witness=w,paths=paths,terminals=sorted({p['terminal'] for p in paths}),status='CONDITIONAL_PATHS' if paths else 'NO_COMPATIBLE_PATH')


def verify_measured_occurrence_paths(m,measurements,root,hops,c,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        try:
            view=snapshot(m)
            if set(c)!={'policy','root','hops','witness','paths','terminals','status'} or c['policy']!='measured_occurrence_paths_v1' or canonical(c['root'])!=canonical(root) or type(c['hops']) is not int or c['hops']!=hops:return False
            w=c['witness']
            if not verify_acquisition_witness(view,measurements,w):return False
            sources,ids=_inputs(view,w,root,hops);paths=[]
            pending=[(root['source'],)]
            while pending:
                budget.consume();seq=pending.pop()
                if len(seq)==hops:
                    paths.append(dict(sources=list(seq),occurrences=[[ids[s,0],ids[s,1]] for s in seq],joins=[[ids[a,1],ids[b,0]] for a,b in zip(seq,seq[1:])],terminal=decode(view.episodes[seq[-1]][0][1])))
                    continue
                a=seq[-1];ra=w['measurements'][ids[a,1]]
                for b in reversed(sources):
                    budget.consume();rb=w['measurements'][ids[b,0]]
                    if a==b or ra['clock']!=rb['clock'] or ra['upper']<rb['lower'] or rb['upper']<ra['lower'] or view.episodes[a][0][1]!=view.episodes[b][0][0]:continue
                    pending.append(seq+(b,))
            return canonical(c['paths'])==canonical(paths) and canonical(c['terminals'])==canonical(sorted({p['terminal'] for p in paths})) and c['status']==('CONDITIONAL_PATHS' if paths else 'NO_COMPATIBLE_PATH')
        except (TypeError,ValueError,KeyError,IndexError,AttributeError):return False

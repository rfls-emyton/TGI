"""Exact compact representation of finite measured occurrence-path sets.

Counts use canonical nonnegative decimal strings. Graph plus root/hop scope,
not terminal counts alone, preserves every source sequence and its provenance.
"""
from tgi.acquisition_witness import certify_acquisition_witness,verify_acquisition_witness
from tgi.measured_occurrence_path import _inputs
from tgi.organization_snapshot import snapshot
from tgi.role_work import RoleSearchBudget
from tgi.frame_engine import canonical
from tgi.identity import decode


def _decimal_count(value):
    """Exact canonical decimal without changing Python's global digit limit."""
    if value==0:return '0'
    blocks=[]
    while value:
        value,remainder=divmod(value,1000000000);blocks.append(remainder)
    return str(blocks[-1])+''.join(format(b,'09d') for b in reversed(blocks[:-1]))


def _read_count(text):
    """Read canonical ASCII decimal counts without a global digit-limit change."""
    if not isinstance(text, str) or not text or (len(text) > 1 and text[0] == '0'):
        raise ValueError('Canonical nonnegative ASCII decimal required')
    budget = RoleSearchBudget()
    for character in text:
        budget.consume()
        if not '0' <= character <= '9':
            raise ValueError('Canonical nonnegative ASCII decimal required')
    value = 0
    for start in range(0, len(text), 9):
        budget.consume()
        block = text[start:start+9]
        value = value * 10**len(block) + int(block)
    return value


def certify_compact_measured_paths(m,records,root,hops,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        v=snapshot(m);w=certify_acquisition_witness(v,records);sources,ids=_inputs(v,w,root,hops);pairs={frozenset((p['left'],p['right'])) for p in w['pairs']};edges=[]
        for a in sources:
          for b in sources:
            budget.consume()
            if v.episodes[a][0][1]==v.episodes[b][0][0] and frozenset((ids[a,1],ids[b,0])) in pairs:edges.append(dict(source=a,target=b,join=[ids[a,1],ids[b,0]]))
        counts={s:int(s==root['source']) for s in sources}
        for _ in range(hops-1):
            budget.consume();new={s:0 for s in sources}
            for edge in edges:budget.consume();new[edge['target']]+=counts[edge['source']]
            counts=new
            if not any(counts.values()):break
        nodes=[dict(source=s,occurrences=[ids[s,0],ids[s,1]]) for s in sources]
        terminal_counts=[dict(source=s,occurrence=ids[s,1],text=decode(v.episodes[s][0][1]),count=_decimal_count(counts[s])) for s in sources]
        return dict(policy='compact_measured_paths_v1',root=dict(root),hops=hops,witness=w,nodes=nodes,edges=edges,terminal_counts=terminal_counts,total=_decimal_count(sum(counts.values())))


def verify_compact_measured_paths(m,records,root,hops,c,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        try:
            v=snapshot(m)
            if set(c)!={'policy','root','hops','witness','nodes','edges','terminal_counts','total'} or c['policy']!='compact_measured_paths_v1' or canonical(c['root'])!=canonical(root) or type(c['hops']) is not int or c['hops']!=hops:return False
            w=c['witness']
            if not verify_acquisition_witness(v,records,w):return False
            sources,ids=_inputs(v,w,root,hops);expected_nodes=[dict(source=s,occurrences=[ids[s,0],ids[s,1]]) for s in sources];edges=[]
            for a in sources:
              for b in sources:
                budget.consume();ra=w['measurements'][ids[a,1]];rb=w['measurements'][ids[b,0]]
                if a!=b and ra['clock']==rb['clock'] and ra['lower']<=rb['upper'] and rb['lower']<=ra['upper'] and v.episodes[a][0][1]==v.episodes[b][0][0]:edges.append(dict(source=a,target=b,join=[ids[a,1],ids[b,0]]))
            if canonical(c['nodes'])!=canonical(expected_nodes) or canonical(c['edges'])!=canonical(edges):return False
            results=[];total=0
            for target in sources:
                backward={s:int(s==target) for s in sources}
                for _ in range(hops-1):
                    budget.consume();prev={s:0 for s in sources}
                    for edge in edges:budget.consume();prev[edge['source']]+=backward[edge['target']]
                    backward=prev
                    if not any(backward.values()):break
                total+=backward[root['source']]
                results.append(dict(source=target,occurrence=ids[target,1],text=decode(v.episodes[target][0][1]),count=_decimal_count(backward[root['source']])))
            return canonical(c['terminal_counts'])==canonical(results) and type(c['total']) is str and c['total']==_decimal_count(total)
        except (KeyError,IndexError,TypeError,ValueError,AttributeError):return False

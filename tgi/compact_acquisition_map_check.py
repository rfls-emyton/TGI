from tgi.compact_measured_path import _read_count
"""Verify complete reachable assignment closure, not a producer rerun."""
from .identity import encode,decode
from .organization import OMEGA_CRIT
from .organization_snapshot import snapshot
from .acquisition_witness import verify_acquisition_witness
from .role_work import RoleSearchBudget
from .frame_engine import canonical
from .compact_measured_path import _decimal_count

def _graph(g,left,right,alignments,direction,budget):
    if set(g)!={'direction','nodes','edges','terminals'} or type(g['direction']) is not int or g['direction']!=direction:raise ValueError('Graph schema')
    nodes=g['nodes'];keys=[];lookup={}
    for i,node in enumerate(nodes):
        budget.consume()
        if set(node)!={'mask','mapping','count'} or type(node['mask']) is not int or not 0<=node['mask']<(1<<len(right)):raise ValueError('State schema')
        items=tuple(tuple(p) for p in node['mapping'])
        if any(len(p)!=2 or any(type(x) is not int for x in p) for p in items) or items!=tuple(sorted(set(items))) or len({x for x,y in items})!=len(items) or len({y for x,y in items})!=len(items):raise ValueError('Invalid state relation')
        key=(node['mask'],items)
        if key in lookup:raise ValueError('Duplicate state')
        lookup[key]=i;keys.append(key)
    if not keys or keys[0]!=(0,()):raise ValueError('Missing root')
    index={(a['left'],a['right'],a['direction']):k for k,a in enumerate(alignments)};edges=[]
    for source,(mask,items) in enumerate(keys):
        i=mask.bit_count()
        if i==len(left):continue
        for j in range(len(right)):
            budget.consume()
            aid=index.get((i,j,direction))
            if mask&(1<<j) or aid is None:continue
            pairs=set(items)
            for u,v,_,_ in alignments[aid]['positions']:budget.consume();pairs.add((u,v))
            if len({x for x,y in pairs})!=len(pairs) or len({y for x,y in pairs})!=len(pairs):continue
            key=(mask|(1<<j),tuple(sorted(pairs)))
            if key not in lookup:raise ValueError('Omitted continuation')
            edges.append([source,lookup[key],aid])
    if canonical(edges)!=canonical(g['edges']):raise ValueError('Incomplete transition inventory')
    incoming=[[] for _ in nodes]
    for a,b,_ in edges:incoming[b].append(a)
    counts=[0]*len(nodes);counts[0]=1
    for i in sorted(range(1,len(nodes)),key=lambda i:keys[i][0].bit_count()):
        budget.consume();counts[i]=sum(counts[a] for a in incoming[i])
    if any(v==0 for v in counts) or any(nodes[i]['count']!=_decimal_count(v) for i,v in enumerate(counts)):raise ValueError('Unreachable state or incorrect multiplicity')
    terminals=[i for i,(mask,_) in enumerate(keys) if mask.bit_count()==len(left)]
    if canonical(terminals)!=canonical(g['terminals']):raise ValueError('Terminal scope')
    return terminals

def verify_compact_acquisition_map(model,measurements,left,right,query,c,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
      try:
        if not isinstance(c,dict) or set(c)!={'policy','threshold','query','left','right','witness','alignments','graphs','outcomes','alternative_count','diversity','status','outputs','output'} or c['policy']!='compact_acquisition_assignment_v1' or type(c['threshold']) is not int or c['threshold']!=OMEGA_CRIT:return False
        m=snapshot(model);q=encode(query)
        if not q or not isinstance(left,list) or not isinstance(right,list) or len(set(left))!=len(left) or len(set(right))!=len(right) or set(left)&set(right) or set(left)|set(right)!=set(m.episodes):return False
        if not verify_acquisition_witness(m,measurements,c['witness']):return False
        records={r['source']:r for r in measurements}
        if len(records)!=len(measurements) or set(records)!=set(m.episodes):return False
        for s,(frames,_) in m.episodes.items():
            budget.consume();r=records[s]
            if len(frames)!=1 or (r['frame'],r['start'],r['stop'])!=(0,0,len(frames[0])):return False
        left=sorted(left);right=sorted(right)
        if c['query']!=query or canonical(c['left'])!=canonical(left) or canonical(c['right'])!=canonical(right):return False
        clocks={r['clock'] for r in measurements};enabled=len(left)==len(right) and len(clocks)==1;alignments=[]
        if enabled:
          for i,a in enumerate(left):
           for j,b in enumerate(right):
            budget.consume()
            if records[a]['upper']<records[b]['lower'] or records[b]['upper']<records[a]['lower']:continue
            alignments.append(dict(left=i,right=j,direction=0,positions=[]));x=m.episodes[a][0][0];y=m.episodes[b][0][0]
            if len(x)!=len(y):continue
            for sign in (-1,1):
                positions=[]
                for k,u in enumerate(x):budget.consume();p=k if sign==1 else len(x)-1-k;positions.append([u,y[p],k,p])
                alignments.append(dict(left=i,right=j,direction=sign,positions=positions))
        if canonical(c['alignments'])!=canonical(alignments) or len(c['graphs'])!=(3 if enabled else 0):return False
        outcomes=[]
        for g,sign in zip(c['graphs'],(0,-1,1)):
            terminals=_graph(g,left,right,alignments,sign,budget)
            if not sign:continue
            for terminal in terminals:
                node=g['nodes'][terminal];mapping=dict(node['mapping']);missing=set();output=[]
                for k in range(len(q)):
                    budget.consume();u=q[k if sign==1 else len(q)-1-k]
                    if u not in mapping:missing.add(u)
                    else:output.append(mapping[u])
                outcomes.append(dict(direction=sign,terminal=terminal,count=node['count'],missing=sorted(missing),output=None if missing else decode(tuple(output))))
        count=sum(_read_count(o['count']) for o in outcomes);outputs=sorted({o['output'] for o in outcomes if o['output'] is not None});distinct=len({m.episodes[s][0][0] for s in left})
        status='INCOMPLETE' if len(left)!=len(right) else 'CLOCK_UNDETERMINED' if len(clocks)!=1 else 'CONFLICT' if not count else 'INCOMPLETE' if distinct<OMEGA_CRIT else 'UNKNOWN_ID' if any(o['missing'] for o in outcomes) else 'AMBIGUOUS_OUTPUT' if len(outputs)!=1 else 'CONDITIONAL_OUTPUT'
        expected=dict(outcomes=outcomes,alternative_count=_decimal_count(count),diversity=distinct,status=status,outputs=outputs,output=outputs[0] if status=='CONDITIONAL_OUTPUT' else None)
        return all(canonical(c[k])==canonical(v) for k,v in expected.items())
      except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

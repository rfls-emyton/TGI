"""Neutral original-occurrence layout; no context selection or output prediction."""
from .identity import encode,decode
from .incidence import _endpoint


def layout(view,groups,measurements,root_port,budget,*,allow_partial=False):
    if not isinstance(groups,list) or not groups:raise ValueError('Complete groups required')
    lookup={(r['source'],r['frame']):r for r in measurements}
    expected={(s,i) for s,(frames,_) in view.episodes.items() for i in range(len(frames))}
    if len(lookup)!=len(measurements) or set(lookup)!=expected:raise ValueError('Complete frame measurement coverage required')
    rows=[];used=set();ports=None;windows=[]
    for group in groups:
        budget.consume();cells={};bounds=set();actions=set();before_intervals=[];certain=True
        if not isinstance(group,list) or not group:raise ValueError('Nonempty group required')
        for spec in group:
            budget.consume()
            if not isinstance(spec,dict) or set(spec)!={'port','source'}:raise ValueError('Exact original interface layout required')
            port,source=spec['port'],spec['source']
            if not isinstance(port,str) or not port or not isinstance(source,str) or source not in view.episodes or source in used or port in cells:raise ValueError('Invalid original source/interface')
            encode(port);used.add(source);frames=view.episodes[source][0]
            if len(frames)!=3:raise ValueError('Before/action/after required')
            ms=[lookup[source,i] for i in range(3)]
            if any(r['start']!=0 or r['stop']!=len(frames[i]) for i,r in enumerate(ms)):raise ValueError('Whole-frame coverage required')
            before,action,after=ms;actions.add(frames[1]);bounds.add((action['clock'],action['lower'],action['upper']));before_intervals.append((before['clock'],before['lower'],before['upper']))
            certain &= len({r['clock'] for r in ms})==1 and before['upper']<=action['lower'] and action['upper']<=after['lower']
            cells[port]={'source':source,'frames':list(map(decode,frames)), 'occurrences':[_endpoint(view,source,(i,0,len(f))) for i,f in enumerate(frames)],'measurements':ms}
        if len(actions)!=1 or len(bounds)!=1:raise ValueError('One shared raw action and actuation required')
        if ports is None:ports=sorted(cells)
        if not allow_partial and sorted(cells)!=ports:raise ValueError('Complete common interface inventory required')
        bound=next(iter(bounds));clock=bound[0]
        certain &= all(c==clock for c,_,_ in before_intervals) and max(lo for _,lo,_ in before_intervals)<=min(hi for _,_,hi in before_intervals)
        rows.append({'cells':cells,'certain':bool(certain)});windows.append(bound)
    if allow_partial:ports=sorted({p for row in rows for p in row['cells']})
    if used!=set(view.episodes) or root_port not in ports:raise ValueError('Complete original domain and target required')
    for index,row in enumerate(rows):
        budget.consume()
        for cell in row['cells'].values():
            before,_,after=cell['measurements']
            if any(clock!=before['clock'] or not (hi<before['lower'] or lo>after['upper']) for j,(clock,lo,hi) in enumerate(windows) if j!=index):row['certain']=False
    return ports,rows


def query_values(ports,root_port,before,action,context):
    if not isinstance(before,str) or not before or not isinstance(action,str) or not action:raise ValueError('Nonempty raw query required')
    encode(before);encode(action)
    if not isinstance(context,dict) or set(context)!=set(ports)-{root_port}:raise ValueError('Complete raw context query required')
    for value in context.values():
        if not isinstance(value,str) or not value:raise ValueError('Nonempty raw context value required')
        encode(value)

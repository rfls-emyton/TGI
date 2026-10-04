"""Evidence-scoped correspondence across multiple organization axes."""
from .organization import _match, OMEGA_CRIT
from .organization_snapshot import snapshot
from .incidence import _endpoint
from .frame_engine import canonical

def _ports(ports):
    if not isinstance(ports,(list,tuple)) or len(ports)<2:
        raise ValueError('At least two distinct organization-axis ports required')
    result=[]
    for port in ports:
        if not isinstance(port,(list,tuple)) or len(port)!=2 or not isinstance(port[0],str) or type(port[1]) is not int or port[1]<0:
            raise ValueError('Invalid organization-axis port')
        result.append(tuple(port))
    if len(set(result))!=len(result):raise ValueError('Duplicate port')
    return tuple(result)

def joint_correspondence(engine,ports):
    ports=_ports(ports)
    result={'status':'NO_PATH','ports':[list(p) for p in ports],'supports':[],'diversity':0,'witnesses':[],'uncertain':[]}
    if engine._dirty:result['status']='INCOMPLETE';return result
    engine=snapshot(engine)
    if any(a in engine.rejected_organizations for a,_ in ports):result['status']='AMBIGUOUS';return result
    if any(a not in engine.organizations for a,_ in ports):return result
    organizations=[engine.organizations[a] for a,_ in ports]
    if any(axis>=len(h.diversity) for h,(_,axis) in zip(organizations,ports)):raise ValueError('Axis outside organization')
    if any(a!=h.anchor or not engine._phase_valid(h) for h,(a,_) in zip(organizations,ports)):
        result['status']='INCOMPLETE';return result
    values=set();agreements=[]
    for source,(frames,_) in sorted(engine.episodes.items()):
        if any(len(frames)!=len(h.pattern) for h in organizations):continue
        matches=[_match(h.pattern,frames) for h in organizations]
        if any(not m for m in matches):continue
        if any(len(m)!=1 for m in matches):
            result['uncertain'].append({'source':source,'match_counts':[len(m) for m in matches]});continue
        spans=[]
        for h,(_,axis),m in zip(organizations,ports,matches):
            spans.append(tuple(sorted((f,start,stop) for (f,p),(start,stop) in m[0][1].items() if h.pattern[f][p]==('axis',axis))))
        agrees=bool(spans[0]) and all(s==spans[0] for s in spans)
        agreements.append(agrees);values.add(matches[0][0][0][ports[0][1]])
        result['supports'].append(source)
        result['witnesses'].append({'source':source,'occurrences':[[ _endpoint(engine,source,s) for s in group] for group in spans]})
    result['diversity']=len(values)
    if result['uncertain'] or (any(agreements) and not all(agreements)):result['status']='AMBIGUOUS'
    elif agreements and all(agreements):result['status']='LINKED' if len(values)>=OMEGA_CRIT else 'INCOMPLETE'
    return result

def verify_joint_correspondence(engine,result):
    """Check all common observations independently of the generator."""
    try:
        ports=_ports(result['ports'])
        if engine._dirty or result['status']!='LINKED' or result['uncertain']:return False
        engine=snapshot(engine);organizations=[]
        for anchor,axis in ports:
            if anchor in engine.rejected_organizations:return False
            h=engine.organizations[anchor]
            if anchor!=h.anchor or axis>=len(h.diversity) or not engine._phase_valid(h):return False
            organizations.append(h)
        rows=[];values=set()
        for source,(frames,_) in sorted(engine.episodes.items()):
            if any(len(frames)!=len(h.pattern) for h in organizations):continue
            matches=[_match(h.pattern,frames) for h in organizations]
            if any(not m for m in matches):continue
            if any(len(m)!=1 for m in matches):return False
            all_spans=[]
            for h,(_,axis),m in zip(organizations,ports,matches):
                group=tuple(sorted((f,a,b) for (f,p),(a,b) in m[0][1].items() if h.pattern[f][p]==('axis',axis)))
                if not group or (all_spans and group!=all_spans[0]):return False
                all_spans.append(group)
            values.add(matches[0][0][0][ports[0][1]])
            rows.append({'source':source,'occurrences':[[_endpoint(engine,source,s) for s in group] for group in all_spans]})
        return len(values)>=OMEGA_CRIT and type(result['diversity']) is int and result['diversity']==len(values) and result['supports']==[r['source'] for r in rows] and canonical(result['witnesses'])==canonical(rows)
    except (KeyError,ValueError,TypeError,IndexError,AttributeError):return False

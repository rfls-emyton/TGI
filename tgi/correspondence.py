"""Observed scope-bound correspondence of axis occurrence sets."""
from .organization import _match, OMEGA_CRIT
from .organization_snapshot import snapshot
from .frame_engine import canonical
from .incidence import _endpoint


def _spans(h,locations,axis):
    return tuple(sorted((f,a,b) for (f,p),(a,b) in locations.items() if h.pattern[f][p]==("axis",axis)))


def axis_correspondence(engine, left, axis, right):
    if not isinstance(left,str) or not isinstance(right,str) or type(axis) is not int or axis<0:
        raise ValueError("Correspondence requires organization anchors and a nonnegative axis")
    result={"status":"NO_PATH","left":left,"left_axis":axis,"right":right,"right_axis":None,
            "supports":[],"diversity":0,"witnesses":[],"uncertain":[]}
    if engine._dirty:
        result["status"]="INCOMPLETE";return result
    engine=snapshot(engine)
    if left in engine.rejected_organizations or right in engine.rejected_organizations:
        result["status"]="AMBIGUOUS";return result
    if left not in engine.organizations or right not in engine.organizations:
        return result
    h,j=engine.organizations[left],engine.organizations[right]
    if axis>=len(h.diversity):
        raise ValueError("Axis outside left organization")
    if left!=h.anchor or right!=j.anchor or not engine._phase_valid(h) or not engine._phase_valid(j):
        result["status"]="INCOMPLETE";return result
    candidates=set(range(len(j.diversity)));seen=set();values=set();rows=[]
    for source,(frames,_) in sorted(engine.episodes.items()):
        if len(frames)!=len(h.pattern) or len(frames)!=len(j.pattern):continue
        hm,jm=_match(h.pattern,frames),_match(j.pattern,frames)
        if not hm or not jm:continue
        if len(hm)!=1 or len(jm)!=1:
            result["uncertain"].append({"source":source,"left_matches":len(hm),"right_matches":len(jm)})
            continue
        bindings,locations=hm[0];other_locations=jm[0][1]
        spans=_spans(h,locations,axis)
        matches={k for k in range(len(j.diversity)) if spans==_spans(j,other_locations,k)}
        candidates &= matches;seen |= matches;values.add(bindings[axis])
        rows.append({"source":source,"right_axes":sorted(matches),"occurrences":[_endpoint(engine,source,s) for s in spans]})
    result["supports"]=[row["source"] for row in rows];result["diversity"]=len(values);result["witnesses"]=rows
    if result["uncertain"] or (seen and len(candidates)!=1):
        result["status"]="AMBIGUOUS"
    elif rows and len(candidates)==1:
        if len(values)<OMEGA_CRIT:result["status"]="INCOMPLETE"
        else:result["status"]="LINKED";result["right_axis"]=next(iter(candidates))
    return result


def verify_correspondence(engine,result):
    """Independent complete-scope check, never calls axis_correspondence."""
    try:
        if engine._dirty or result["status"]!="LINKED" or result["uncertain"]:return False
        engine=snapshot(engine)
        left,right=result["left"],result["right"];a,b=result["left_axis"],result["right_axis"]
        if type(a) is not int or type(b) is not int or min(a,b)<0:return False
        if left in engine.rejected_organizations or right in engine.rejected_organizations:return False
        h,j=engine.organizations[left],engine.organizations[right]
        if left!=h.anchor or right!=j.anchor or a>=len(h.diversity) or b>=len(j.diversity):return False
        if not engine._phase_valid(h) or not engine._phase_valid(j):return False
        expected=[];values=set()
        for source,(frames,_) in sorted(engine.episodes.items()):
            if len(frames)!=len(h.pattern) or len(frames)!=len(j.pattern):continue
            hm,jm=_match(h.pattern,frames),_match(j.pattern,frames)
            if not hm or not jm:continue
            if len(hm)!=1 or len(jm)!=1:return False
            spans=tuple(sorted((f,start,stop) for (f,p),(start,stop) in hm[0][1].items() if h.pattern[f][p]==("axis",a)))
            target=tuple(sorted((f,start,stop) for (f,p),(start,stop) in jm[0][1].items() if j.pattern[f][p]==("axis",b)))
            if not spans or spans!=target:return False
            values.add(hm[0][0][a])
            expected.append({"source":source,"right_axes":[b],"occurrences":[_endpoint(engine,source,s) for s in spans]})
        return (len(values)>=OMEGA_CRIT and type(result["diversity"]) is int and result["diversity"]==len(values)
                and result["supports"]==[r["source"] for r in expected]
                and canonical(result["witnesses"])==canonical(expected))
    except (ValueError,KeyError,IndexError,TypeError,AttributeError):return False

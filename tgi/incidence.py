"""Phase-bound links between observed axis occurrences, without semantic labels."""
from .frame_engine import canonical
from .organization import _match
from .organization_snapshot import snapshot
from .phase_evidence import validate_organization, oppositions


def _query(engine, source, frame, start, stop):
    if not isinstance(source, str) or any(type(x) is not int for x in (frame,start,stop)):
        raise ValueError("Occurrence requires source and integer frame/start/stop")
    if min(frame,start) < 0 or stop <= start:
        raise ValueError("Occurrence interval must be nonempty and nonnegative")
    if source not in engine.episodes:
        return False
    frames = engine.episodes[source][0]
    if frame >= len(frames) or stop > len(frames[frame]):
        raise ValueError("Occurrence outside observed frame")
    return True


def _endpoint(engine, source, span):
    fi,start,stop = span
    frames,receipts = engine.episodes[source]
    origin = receipts[fi].origin
    offset = sum(len(frame) for frame in frames[:fi])
    return {"frame":fi,"start":start,"stop":stop,"event_span":[offset+start,offset+stop],
            "identities":list(frames[fi][start:stop]),
            "coordinates":[list((origin[0]+pos,)+origin[1:]) for pos in range(start,stop)]}


def _rows(engine, source, query):
    frames = engine.episodes[source][0]
    rows, blocked, uncertain = [], [], []
    # Inspect both active and rejected organizations so rejection cannot silently
    # erase an alternative. Unrelated organizations do not create a link.
    entries = [(key,h,False,None) for key,h in engine.organizations.items()]
    entries += [(key,h,True,opposing) for key,(h,opposing) in engine.rejected_organizations.items()]
    for key,h,rejected,opposing in sorted(entries, key=lambda item:item[0]):
        matches = _match(h.pattern,frames) if len(h.pattern)==len(frames) else []
        if len(matches)>1 and any((f,a,b)==query for _,loc in matches for (f,p),(a,b) in loc.items()):
            if key!=h.anchor:
                raise ValueError("Invalid incidence organization anchor")
            if rejected:
                valid=(validate_organization(engine,h,require_consistent=False) and bool(opposing)
                       and opposing==oppositions(h.pattern,sorted(engine.episodes.items())))
            else:
                valid=engine._phase_valid(h)
            if not valid:
                raise ValueError("Uncertain incidence requires live phase evidence")
            uncertain.append({"anchor":key,"match_count":len(matches),"reason":"multiple_interval_bindings"})
            continue
        if len(matches)!=1:
            continue
        bindings,locations = matches[0]
        axes = {h.pattern[f][p][1] for (f,p),(start,stop) in locations.items() if (f,start,stop)==query}
        if not axes:
            continue
        if key!=h.anchor or source not in h.supports:
            raise ValueError("Invalid incidence organization ownership")
        if rejected:
            if (not validate_organization(engine,h,require_consistent=False) or not opposing
                or opposing!=oppositions(h.pattern,sorted(engine.episodes.items()))):
                raise ValueError("Invalid opposing phase evidence")
            blocked.append(key)
            continue
        if not engine._phase_valid(h):
            raise ValueError("Incidence requires live phase evidence")
        for axis in sorted(axes):
            spans = sorted({(f,start,stop) for (f,p),(start,stop) in locations.items()
                            if h.pattern[f][p]==("axis",axis) and (f,start,stop)!=query})
            rows.append({"anchor":key,"axis":axis,"targets":[_endpoint(engine,source,s) for s in spans]})
    return rows,blocked,uncertain


def _directed(targets, origin, direction):
    if direction == "all":return targets
    if direction == "forward":return [p for p in targets if p["event_span"][0]>=origin["event_span"][1]]
    return [p for p in targets if p["event_span"][1]<=origin["event_span"][0]]


def trace_incidence(engine, source, frame, start, stop, *, direction="all"):
    """Follow observed co-variation links; does not form or mutate experience."""
    if direction not in ("all","forward","backward"):
        raise ValueError("Incidence direction must be all, forward or backward")
    exists = _query(engine,source,frame,start,stop)
    result = {"direction":direction,"status":"NO_PATH","source":source,"origin":None,"targets":[],"witnesses":[],"blocked":[],"uncertain":[]}
    if not exists:
        return result
    if engine._dirty:
        result["status"]="INCOMPLETE"; return result
    engine = snapshot(engine)
    if not engine._alive(source):
        result["status"]="INCOMPLETE"; return result
    result["origin"] = _endpoint(engine,source,(frame,start,stop))
    try:
        rows,blocked,uncertain = _rows(engine,source,(frame,start,stop))
    except (ValueError,KeyError,IndexError,TypeError):
        result["status"]="INCOMPLETE"; return result
    result["witnesses"],result["blocked"],result["uncertain"] = rows,blocked,uncertain
    target_sets = {tuple((p["frame"],p["start"],p["stop"]) for p in row["targets"]) for row in rows}
    if blocked or uncertain or len(target_sets)>1:
        result["status"]="AMBIGUOUS"
    elif target_sets and next(iter(target_sets)):
        result["targets"]=_directed(rows[0]["targets"],result["origin"],direction)
        if result["targets"]:result["status"]="LINKED"
    return result


def verify_incidence(engine, result):
    """Verify a complete LINKED certificate without calling trace_incidence."""
    try:
        if engine._dirty or result["status"]!="LINKED" or result["blocked"] or result.get("uncertain"):
            return False
        direction=result.get("direction","all")
        if direction not in ("all","forward","backward"):return False
        engine=snapshot(engine)
        source=result["source"];origin=result["origin"]
        query=(origin["frame"],origin["start"],origin["stop"])
        if not _query(engine,source,*query) or not engine._alive(source):
            return False
        if canonical(origin)!=canonical(_endpoint(engine,source,query)):
            return False
        expected=[];full_targets=None
        frames=engine.episodes[source][0]
        for key,h in sorted(engine.organizations.items()):
            matches=_match(h.pattern,frames) if len(h.pattern)==len(frames) else []
            if len(matches)>1 and any((f,a,b)==query for _,loc in matches for (f,p),(a,b) in loc.items()):
                return False
            if len(matches)!=1:
                continue
            _,locations=matches[0]
            for (f,p),(start,stop) in sorted(locations.items()):
                if (f,start,stop)!=query:
                    continue
                axis=h.pattern[f][p][1]
                if key!=h.anchor or source not in h.supports or not engine._phase_valid(h):
                    return False
                spans=sorted({(g,a,b) for (g,q),(a,b) in locations.items()
                              if h.pattern[g][q]==("axis",axis) and (g,a,b)!=query})
                targets=[_endpoint(engine,source,s) for s in spans]
                if not targets or (full_targets is not None and canonical(targets)!=canonical(full_targets)):
                    return False
                full_targets=targets
                selected=[p for p in targets if direction=="all" or
                          (direction=="forward" and p["event_span"][0]>=origin["event_span"][1]) or
                          (direction=="backward" and p["event_span"][1]<=origin["event_span"][0])]
                if not selected or canonical(selected)!=canonical(result["targets"]):return False
                expected.append({"anchor":key,"axis":axis,"targets":targets})
        for h,_ in engine.rejected_organizations.values():
            matches=_match(h.pattern,frames) if len(h.pattern)==len(frames) else []
            if any((f,a,b)==query for _,loc in matches for (f,p),(a,b) in loc.items()):
                return False
        return bool(expected) and canonical(expected)==canonical(result["witnesses"])
    except (ValueError,KeyError,IndexError,TypeError,AttributeError):
        return False

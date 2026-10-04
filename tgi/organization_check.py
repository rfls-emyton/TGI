"""Independent checker: never calls RawOrganization.resolve or ask."""
from .identity import encode
from .organization import _match


def _trace_ownership(engine, h, raw, proof):
    for bindings, locations in _match(h.pattern, raw):
        valid = True
        for fi, trace in enumerate(proof["characters"], len(raw)):
            cursor = 0
            for pi, (kind, value) in enumerate(h.pattern[fi]):
                length = len(value if kind == "lit" else bindings[value])
                for offset, point in enumerate(trace[cursor:cursor+length]):
                    if kind == "axis":
                        allowed = {(f, start+offset) for (f, part), (start, stop) in locations.items()
                                   if h.pattern[f][part] == ("axis", value)}
                        valid &= point["kind"] == "trigger" and (point["frame"], point["position"]) in allowed
                    else:
                        if point["kind"] != "crystal" or point["source"] not in h.supports:
                            valid = False; continue
                        source_frames = engine.episodes[point["source"]][0]
                        starts = {sum(len(v if k == "lit" else sb[v]) for k, v in h.pattern[fi][:pi])
                                  for sb, _ in _match(h.pattern, source_frames)}
                        valid &= point["frame"] == fi and any(point["position"] == start+offset for start in starts)
                cursor += length
            valid &= cursor == len(trace)
        if valid:
            return True
    return False


def _verify_character_trace(engine, h, raw, proof, output, view):
    if not _trace_ownership(engine, h, raw, proof):
        return False
    if tuple(proof["supports"]) != h.supports or len(proof["characters"]) != len(output):
        return False
    for ids, trace in zip(output, proof["characters"]):
        if len(ids) != len(trace):
            return False
        for identity, point in zip(ids, trace):
            fi, pos = point["frame"], point["position"]
            if type(fi) is not int or type(pos) is not int or min(fi, pos) < 0:
                return False
            if point["kind"] == "trigger":
                if raw[fi][pos] != identity:
                    return False
            elif point["kind"] == "crystal":
                if point["source"] not in h.supports:
                    return False
                frames, receipts = engine.episodes[point["source"]]
                origin = receipts[fi].origin
                coord = (origin[0]+pos,)+origin[1:]
                if (tuple(point["coordinate"]) != coord or any(type(x) is not int for x in point["coordinate"]) or frames[fi][pos] != identity or
                    view.atoms[coord].identity != identity):
                    return False
            else:
                return False
    return True


def verify_resolution(engine, prefix, result, *, terminal_only=False):
    try:
        if engine._dirty or result["status"] != "RESOLVED" or not result["proofs"]:
            return False
        raw = tuple(encode(f) for f in prefix)
        output = tuple(encode(f) for f in result["output"])
        allowed, anchors = set(), set()
        for anchor, h in engine.organizations.items():
            if len(raw) >= len(h.pattern) or (terminal_only and len(h.pattern) != len(raw)+1):
                continue
            for bindings, _ in _match(h.pattern, raw):
                if anchor != h.anchor or not engine._phase_valid(h) or len(bindings) != len(h.diversity):
                    return False
                continuation = tuple(tuple(identity for kind, value in parts
                                           for identity in (value if kind == "lit" else bindings[value]))
                                     for parts in h.pattern[len(raw):])
                allowed.add(continuation)
                if continuation == output:
                    anchors.add(anchor)
        if allowed != {output}:
            return False
        view = engine.frames.view()
        for proof in result["proofs"]:
            if proof["anchor"] not in anchors or tuple(encode(f) for f in proof["output"]) != output:
                return False
            h = engine.organizations[proof["anchor"]]
            if not _verify_character_trace(engine,h,raw,proof,output,view):
                return False
        return True
    except (KeyError, IndexError, TypeError, ValueError):
        return False


def _verify_refusal_view(engine, prefix, result, *, terminal_only=False):
    """Certify NO_PATH or AMBIGUOUS against the complete current organization.

    Instrument ceilings and broken evidence are INCOMPLETE, never proof of
    absence. This checker does not call resolve/ask or perform formation.
    """
    from .identity import decode
    from .frame_engine import canonical
    from .organization_snapshot import _Snapshot
    from .phase_evidence import validate_organization, oppositions
    try:
        if type(engine) is not _Snapshot or engine._dirty or result["status"] not in ("NO_PATH","AMBIGUOUS") or result["output"]!=[]:
            return False
        raw=tuple(encode(f) for f in prefix)
        outputs=set();allowed={};unbound=False
        for anchor,h in sorted(engine.organizations.items()):
            if len(raw)>=len(h.pattern) or (terminal_only and len(h.pattern)!=len(raw)+1):continue
            for bindings,_ in _match(h.pattern,raw):
                if anchor!=h.anchor or not engine._phase_valid(h):return False
                if len(bindings)!=len(h.diversity):unbound=True;continue
                continuation=tuple(tuple(i for k,v in frame for i in (v if k=="lit" else bindings[v])) for frame in h.pattern[len(raw):])
                outputs.add(continuation);allowed.setdefault(anchor,set()).add(continuation)
        revoked=[]
        for anchor,(h,opposing) in sorted(engine.rejected_organizations.items()):
            if len(raw)>=len(h.pattern) or (terminal_only and len(h.pattern)!=len(raw)+1) or not _match(h.pattern,raw):continue
            if (anchor!=h.anchor or not validate_organization(engine,h,require_consistent=False) or not opposing
                or opposing!=oppositions(h.pattern,sorted(engine.episodes.items()))):return False
            revoked.append(anchor)
        status=("AMBIGUOUS" if len(outputs)>1 or (outputs and unbound) else "RESOLVED" if outputs else
                "INCOMPLETE" if unbound else "AMBIGUOUS" if revoked else "NO_PATH")
        if status!=result["status"]:return False
        candidates=[[decode(frame) for frame in out] for out in sorted(outputs)]
        if canonical(result["candidates"])!=canonical(candidates) or result["revoked_candidates"]!=revoked:return False
        covered=set();view=engine.frames.view()
        for proof in result["proofs"]:
            anchor=proof["anchor"];out=tuple(encode(f) for f in proof["output"])
            if out not in allowed.get(anchor,set()):return False
            if not _verify_character_trace(engine,engine.organizations[anchor],raw,proof,out,view):return False
            covered.add(out)
        return covered==outputs
    except (KeyError,IndexError,TypeError,ValueError,AttributeError):return False


def verify_refusal(engine, prefix, result, *, terminal_only=False):
    """Fresh public evidence boundary; internal batches share only their own view."""
    from .organization_snapshot import snapshot
    try:
        return _verify_refusal_view(snapshot(engine), prefix, result, terminal_only=terminal_only)
    except (KeyError, IndexError, TypeError, ValueError, AttributeError):
        return False

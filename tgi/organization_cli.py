"""Raw episode CLI. No schema labels or operator names accepted."""
import json
from .frame_engine import unique_object
from .organization import RawOrganization
from .organization_check import verify_resolution, verify_refusal


def _form(engine, limit):
    from .incremental import FormationSearchLimit
    try:
        engine.form(max_search_steps=limit)
    except FormationSearchLimit as exc:
        return {"status": "INCOMPLETE", "output": [], "reason": "formation_search_limit",
                "search_steps": exc.used, "pending_formation": True,
                "episodes": len(engine.episodes)}
    return None


def run(args):
    from .incremental import SearchBudget
    limit = getattr(args, "max_formation_steps", None)
    SearchBudget(limit)
    SearchBudget(getattr(args,"max_verification_match_steps",None))
    if args.command == "raw-upgrade":
        if args.input.resolve() == args.state.resolve() or args.state.exists():
            raise ValueError("Upgrade requires a distinct new checkpoint; preserve the original")
        engine = RawOrganization.load(args.input, allow_legacy=True, defer_formation=True)
        stopped = _form(engine, limit)
        if stopped is not None:
            return stopped
        engine.save(args.state)
        return engine.inspect()
    if args.command == "raw-learn":
        engine = RawOrganization.load(args.state, defer_formation=True) if args.state.exists() else RawOrganization()
        for line in args.input.read_text(encoding="utf8").splitlines():
            if not line.strip():
                continue
            entry = json.loads(line, object_pairs_hook=unique_object)
            if not isinstance(entry, dict) or set(entry) != {"source_id", "frames"}:
                raise ValueError("Raw episodes accept only source_id and frames")
            engine.observe(entry["source_id"], entry["frames"])
        stopped = _form(engine, limit)
        engine.save(args.state)
        return stopped if stopped is not None else engine.inspect()
    engine = RawOrganization.load(args.state, defer_formation=True)
    stopped = _form(engine, limit)
    if stopped is not None:
        return stopped
    if args.command == "raw-correspondence":
        from .correspondence import axis_correspondence, verify_correspondence
        result = axis_correspondence(engine,args.left,args.axis,args.right)
        result["certificate_verified"] = verify_correspondence(engine,result)
        return result
    if args.command == "raw-incidence":
        from .incidence import trace_incidence, verify_incidence
        result = trace_incidence(engine,args.source,args.frame,args.start,args.stop,direction=args.direction)
        result["certificate_verified"] = verify_incidence(engine,result)
        return result
    if args.command == "raw-inspect":
        return engine.inspect()
    if args.command == "raw-reason":
        from .closure import resolve_closure, verify_closure
        result = resolve_closure(engine, args.text, max_nodes=args.max_nodes, max_work=args.max_work)
        result["certificate_verified"] = verify_closure(engine, args.text, result, max_work=args.max_work)
        return result
    if args.command == "raw-ask":
        return engine.ask(args.text)
    prefix = json.loads(args.frames)
    result = engine.resolve(prefix)
    verification_limit = getattr(args,"max_verification_match_steps",None)
    if verification_limit is None:
        result["certificate_verified"] = verify_resolution(engine, prefix, result) or verify_refusal(engine, prefix, result)
    else:
        from .verification import check_resolution
        result["verification"] = check_resolution(engine,prefix,result,max_match_steps=verification_limit)
        result["certificate_verified"] = result["verification"]["verified"]
    return result

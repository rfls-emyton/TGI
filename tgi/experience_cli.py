import json
from .experience import ExperienceEngine
from .frame_engine import unique_object


def overview(engine):
    keys = sorted({(t.action,t.condition,t.world) for t in engine.causes.trials.values()})
    return {"facts": engine.facts.inspect(), "models": [engine.causes.model(*key) for key in keys],
            "journal_events": len(engine.journal), "crystals": engine.store.frames.inspect()}


def run(args):
    if args.command == "experience-upgrade":
        if args.input.resolve() == args.state.resolve() or args.state.exists():
            raise ValueError("Upgrade requires a new destination; preserve the original checkpoint")
        engine = ExperienceEngine.load(args.input, allow_legacy=True)
        engine.save(args.state)
        return {"upgraded": True, "source_preserved": str(args.input), **overview(engine)}
    if args.command == "experience-learn":
        engine = ExperienceEngine.load(args.state) if args.state.exists() else ExperienceEngine()
        for line in args.input.read_text(encoding="utf8").splitlines():
            if not line.strip():
                continue
            event = json.loads(line, object_pairs_hook=unique_object)
            result = engine.apply(event)
            if event["op"] == "fact" and result["status"] != "RESOLVED":
                raise ValueError("Fact not admitted: "+result["status"])
        engine.save(args.state)
        return overview(engine)
    engine = ExperienceEngine.load(args.state)
    if args.command == "experience-inspect":
        return overview(engine)
    if args.command == "experience-ask":
        result = engine.facts.ask(args.text, args.world)
        return {**result, "certificate_valid": engine.facts.verify(args.text, result, args.world)}
    if args.command == "experience-propose":
        domains = json.loads(args.domains, object_pairs_hook=unique_object)
        return engine.causes.propose_trials(args.action, domains, args.condition, args.world, args.limit)
    before = json.loads(args.before, object_pairs_hook=unique_object)
    if args.command == "experience-predict":
        return engine.causes.predict(args.action, before, args.condition, args.world)
    goal = json.loads(args.goal, object_pairs_hook=unique_object)
    result = engine.causes.plan(before, goal, args.condition, args.world, args.max_depth, args.max_states)
    return {**result, "certificate_valid": engine.causes.verify_plan(before, goal, result, args.condition, args.world)}

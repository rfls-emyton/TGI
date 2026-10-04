from dataclasses import asdict
import json
from .frame_engine import unique_object
from .transport import TransportEngine, verify_certificate


def run(args):
    if args.command == "transport-learn":
        engine = TransportEngine.load(args.state) if args.state.exists() else TransportEngine()
        for line in args.input.read_text(encoding="utf8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line, object_pairs_hook=unique_object)
            if not isinstance(row, dict) or set(row) != {"source_id", "context", "before", "after"}:
                raise ValueError("Each observation requires source_id, context, before, after")
            engine.observe(**row)
        engine.save(args.state)
        return {"contexts": {c: engine.inspect(c) for c in sorted(engine._relations)},
                "scope": "experimental_single_path_transport"}
    engine = TransportEngine.load(args.state)
    if args.command == "transport-inspect":
        return engine.inspect(args.context)
    if args.command == "transport-compose":
        result = engine.compose(args.contexts, args.text)
        return asdict(result)
    result = engine.resolve(args.context, args.text)
    return {**asdict(result), "certificate_valid": verify_certificate(engine, args.context, args.text, result)}

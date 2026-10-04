import argparse
import json
from pathlib import Path
from .identity import REGISTRY_ID, encode
from .provenance import verify_sources


def main():
    parser = argparse.ArgumentParser(description="TGI foundation inspection")
    subs = parser.add_subparsers(dest="command", required=True)
    enc = subs.add_parser("encode", help="Inspect static NMU identities")
    enc.add_argument("text")
    check = subs.add_parser("verify-sources", help="Check source integrity")
    check.add_argument("--root", type=Path, default=Path.cwd())
    form = subs.add_parser("inspect-formation", help="Inspect experimental causal chart; not semantic resolution")
    form.add_argument("text")
    learn = subs.add_parser("relation-learn", help="Experimental affine lattice candidate, not free-language learning")
    learn.add_argument("--input", type=Path, required=True)
    learn.add_argument("--state", type=Path, required=True)
    query = subs.add_parser("relation-query", help="Certified consequence within the affine measurement contract")
    query.add_argument("--state", type=Path, required=True)
    query.add_argument("--context", required=True)
    query.add_argument("--point", nargs=5, type=int, required=True)
    inspect = subs.add_parser("relation-inspect", help="Inspect experimental C/L, Omega, xi, and relation anchor")
    inspect.add_argument("--state", type=Path, required=True)
    inspect.add_argument("--context", required=True)
    ingest = subs.add_parser("ingest", help="Crystallize framed character experiences under the user acceptance contract")
    ingest.add_argument("--input",type=Path,required=True)
    ingest.add_argument("--state",type=Path,required=True)
    fq = subs.add_parser("query", help="Traverse committed crystal atoms with trigger and anchor")
    fq.add_argument("--state",type=Path,required=True)
    fq.add_argument("--trigger",required=True)
    fq.add_argument("--anchor",type=int,required=True)
    fq.add_argument("--max-new",type=int)
    fi = subs.add_parser("inspect", help="Inspect committed frame crystal state and C/L evidence")
    fi.add_argument("--state",type=Path,required=True)
    fi.add_argument("--anchor",type=int)
    tl = subs.add_parser("transport-learn", help="Experimental paired-path learning; explicit operator family")
    tl.add_argument("--input", type=Path, required=True)
    tl.add_argument("--state", type=Path, required=True)
    tq = subs.add_parser("transport-query", help="Resolve a source-absent path with character provenance")
    tq.add_argument("--state", type=Path, required=True)
    tq.add_argument("--context", required=True)
    tq.add_argument("--text", required=True)
    ti = subs.add_parser("transport-inspect", help="Inspect transport hypotheses and evidence")
    ti.add_argument("--state", type=Path, required=True)
    ti.add_argument("--context", required=True)
    tc = subs.add_parser("transport-compose", help="Compose an explicit sequence of learned relations")
    tc.add_argument("--state", type=Path, required=True)
    tc.add_argument("--contexts", nargs="+", required=True)
    tc.add_argument("--text", required=True)
    el = subs.add_parser("experience-learn", help="Ingest grounding, facts, and controlled intervention events")
    el.add_argument("--input", type=Path, required=True)
    el.add_argument("--state", type=Path, required=True)
    eq = subs.add_parser("experience-ask", help="Resolve a raw question through grounded crystal relations")
    eq.add_argument("--state", type=Path, required=True)
    eq.add_argument("--text", required=True)
    eq.add_argument("--world", default="default")
    ei = subs.add_parser("experience-inspect", help="Inspect grounded schemas and intervention models")
    ei.add_argument("--state", type=Path, required=True)
    ep = subs.add_parser("experience-predict", help="Predict a measured action under its stated condition")
    ep.add_argument("--state", type=Path, required=True)
    ep.add_argument("--action", required=True)
    ep.add_argument("--before", required=True, help="JSON sensor state")
    ep.add_argument("--condition", default="default")
    ep.add_argument("--world", default="default")
    eg = subs.add_parser("experience-plan", help="Find an action path to a goal without a supplied action sequence")
    eg.add_argument("--state", type=Path, required=True)
    eg.add_argument("--before", required=True, help="JSON sensor state")
    eg.add_argument("--goal", required=True, help="JSON goal sensor subset")
    eg.add_argument("--condition", default="default")
    eg.add_argument("--world", default="default")
    eg.add_argument("--max-depth", type=int, default=16)
    eg.add_argument("--max-states", type=int, default=10000)
    ex = subs.add_parser("experience-propose", help="Propose unmeasured intervention contrasts without supplying outcomes")
    ex.add_argument("--state", type=Path, required=True)
    ex.add_argument("--action", required=True)
    ex.add_argument("--domains", required=True, help="JSON mapping sensor names to available values")
    ex.add_argument("--condition", default="default")
    ex.add_argument("--world", default="default")
    ex.add_argument("--limit", type=int, default=16)
    eu = subs.add_parser("experience-upgrade", help="Replay a V1 journal with corrected guard derivation into a new checkpoint")
    eu.add_argument("--input", type=Path, required=True)
    eu.add_argument("--state", type=Path, required=True)
    rl = subs.add_parser("raw-learn", help="Form organizations from ordered raw character episodes")
    rl.add_argument("--input", type=Path, required=True)
    rl.add_argument("--state", type=Path, required=True)
    rq = subs.add_parser("raw-ask", help="Resolve a raw question against observed episode prefixes")
    rq.add_argument("--state", type=Path, required=True)
    rq.add_argument("--text", required=True)
    rr = subs.add_parser("raw-resolve", help="Continue an ordered raw episode prefix")
    rr.add_argument("--state", type=Path, required=True)
    rr.add_argument("--frames", required=True, help="JSON array of raw frames")
    rr.add_argument("--max-verification-match-steps", type=int, default=None, help="Optional ceiling on verifier matcher states; not query generation")
    ri = subs.add_parser("raw-inspect", help="Inspect raw organization anchors and source support")
    ri.add_argument("--state", type=Path, required=True)
    rc = subs.add_parser("raw-reason", help="Resolve certified closure across raw episode organizations")
    rc.add_argument("--state", type=Path, required=True)
    rc.add_argument("--text", required=True)
    rc.add_argument("--max-nodes", type=int, default=1024)
    rc.add_argument("--max-work", type=int, default=1000000)
    ru = subs.add_parser("raw-upgrade", help="Explicitly replay V1 raw evidence under phase V2 into a new checkpoint")
    ru.add_argument("--input", type=Path, required=True)
    ru.add_argument("--state", type=Path, required=True)
    rx = subs.add_parser("raw-incidence", help="Trace phase-bound links between observed axis occurrences")
    rx.add_argument("--state", type=Path, required=True)
    rx.add_argument("--source", required=True)
    rx.add_argument("--frame", type=int, required=True)
    rx.add_argument("--start", type=int, required=True)
    rx.add_argument("--stop", type=int, required=True)
    rx.add_argument("--direction", choices=("all","forward","backward"), default="all")
    ry = subs.add_parser("raw-correspondence", help="Trace witnessed axis correspondence between organizations")
    ry.add_argument("--state", type=Path, required=True)
    ry.add_argument("--left", required=True)
    ry.add_argument("--axis", type=int, required=True)
    ry.add_argument("--right", required=True)
    for raw_parser in (rl, rq, rr, ri, rc, ru, rx, ry):
        raw_parser.add_argument("--max-formation-steps", type=int, default=None,
                                help="Ceiling on formation candidate enumeration; not a wall-clock timeout")
    args = parser.parse_args()
    if args.command.startswith("raw-"):
        from .organization_cli import run
        try:
            print(json.dumps(run(args), ensure_ascii=True))
        except (ValueError, TypeError, OSError, KeyError) as error:
            parser.error(str(error))
        return 0
    if args.command.startswith("experience-"):
        from .experience_cli import run
        try:
            print(json.dumps(run(args), ensure_ascii=True))
        except (ValueError, TypeError, OSError) as error:
            parser.error(str(error))
        return 0
    if args.command.startswith("transport-"):
        from .transport_cli import run
        try:
            print(json.dumps(run(args), ensure_ascii=True))
        except (ValueError, TypeError, OSError) as error:
            parser.error(str(error))
        return 0
    if args.command in ("ingest","query","inspect"):
        from .frame_cli import run
        try:
            print(json.dumps(run(args),ensure_ascii=True))
        except (ValueError,TypeError,OSError) as error:
            parser.error(str(error))
        return 0
    if args.command.startswith("relation-"):
        from .relational import RelationalEngine,unique_object
        if args.command == "relation-learn":
            engine = RelationalEngine.load(args.state) if args.state.exists() else RelationalEngine()
            for line in args.input.read_text(encoding="utf8").splitlines():
                if not line.strip():
                    continue
                entry = json.loads(line,object_pairs_hook=unique_object)
                if not isinstance(entry,dict) or set(entry)!={"source_id","raw"}:
                    raise ValueError("Each JSONL entry must contain exactly source_id and raw")
                engine.observe(entry["raw"],entry["source_id"])
            engine.save(args.state)
            contexts = sorted({m.context for m in engine.measurements()})
            print(json.dumps({"scope":"experimental_affine_lattice", "sources":len(engine.measurements()),
                              "contexts":{c:engine.inspect(c) for c in contexts}},ensure_ascii=True))
            return 0
        engine = RelationalEngine.load(args.state)
        if args.command == "relation-inspect":
            print(json.dumps(engine.inspect(args.context),ensure_ascii=True))
            return 0
        print(json.dumps(engine.resolve(args.context,args.point).as_dict(),ensure_ascii=True))
        return 0
    if args.command == "encode":
        print(json.dumps({"registry": REGISTRY_ID, "identities": encode(args.text)}, ensure_ascii=True))
        return 0
    if args.command == "inspect-formation":
        from dataclasses import asdict
        from .events import EventStream
        from .formation import CausalFormation
        model = CausalFormation()
        records = model.observe(EventStream("cli").feed(args.text))
        print(json.dumps({"candidate": "TGI-CAUSAL-RECURRENCE-5D-V1",
                          "scope": "causal_chart_only", "semantic_admission": False,
                          "records": [asdict(r) for r in records],
                          "bond_count": len(model.geometry_snapshot()[0]),
                          "closure_count": len(model.geometry_snapshot()[1])}, ensure_ascii=True))
        return 0
    manifest = json.loads((args.root / "contracts/source_manifest.json").read_text(encoding="utf8"))
    failures = verify_sources(args.root, manifest)
    print(json.dumps({"source_count": len(manifest["sources"]), "mismatches": failures,
                      "scope": "source_integrity_only"}, ensure_ascii=True))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())

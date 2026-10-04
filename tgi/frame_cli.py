"""CLI for the user's frame acceptance contract."""
import json
from dataclasses import asdict
from .frame_engine import FrameEngine,unique_object


def run(args):
    if args.command=="ingest":
        engine=FrameEngine.load(args.state) if args.state.exists() else FrameEngine()
        receipts=[]
        for line in args.input.read_text(encoding="utf8").splitlines():
            if not line.strip():
                continue
            obj=json.loads(line,object_pairs_hook=unique_object)
            if not isinstance(obj,dict) or set(obj)!={"source_id","text"}:
                raise ValueError("Each JSONL record requires exactly source_id and text")
            receipts.append(engine.ingest(obj["text"],obj["source_id"]).as_dict())
        engine.save(args.state)
        return {"state":str(args.state),"receipts":receipts,"engine":engine.inspect()}
    engine=FrameEngine.load(args.state)
    if args.command=="query":
        return asdict(engine.resolve(args.trigger,args.anchor,args.max_new))
    result=engine.inspect()
    result["receipts"]=[receipt.as_dict() for receipt in engine.receipts()
                        if args.anchor is None or receipt.anchor==args.anchor]
    return result

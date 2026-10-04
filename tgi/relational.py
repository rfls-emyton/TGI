"""Integrated candidate for learned affine relations on a discrete 5D lattice.

Scope is explicit: measurement protocol -> exact crystal -> certified coordinate
resolution. This module does not implement free-language semantics.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from hashlib import sha256
import json
import os
import tempfile
from pathlib import Path
from .identity import encode,decode,REGISTRY_ID
from .events import Event
from .exact_field import observation_field
from .bands import Bands

CONTRACT = "TGI-AFFINE-RELATIONAL-V1"


def canonical(value):
    return json.dumps(value,ensure_ascii=True,sort_keys=True,separators=(",", ":"))


def unique_object(pairs):
    obj = {}
    for key,value in pairs:
        if key in obj:
            raise ValueError("Duplicate JSON key")
        obj[key]=value
    return obj


def point(value):
    if not isinstance(value,(tuple,list)) or len(value)!=5 or any(type(x) is not int for x in value):
        raise ValueError("Expected exactly five integer coordinates")
    return tuple(value)


def parse(raw):
    ids = encode(raw)
    obj = json.loads(raw,object_pairs_hook=unique_object)
    if not isinstance(obj,dict) or set(obj)!={"context","input","output"}:
        raise ValueError("Measurement must contain exactly context, input, output")
    if not isinstance(obj["context"],str) or not obj["context"]:
        raise ValueError("Context must be a nonempty measurement scope")
    encode(obj["context"])
    return obj["context"],point(obj["input"]),point(obj["output"]),ids


@dataclass(frozen=True)
class Measurement:
    source_id: str
    raw: str
    context: str
    input: tuple[int,...]
    output: tuple[int,...]
    start: int
    stop: int


@dataclass(frozen=True)
class Answer:
    status: str
    context: str
    input: tuple[int,...]
    output: tuple[int,...] | None = None
    identities: tuple[int,...] = ()
    witnesses: tuple[tuple[str,Q],...] = ()
    anchor: tuple[tuple[Q,...],...] | None = None
    scope: str = "conditional_affine_lattice_consequence"

    def as_dict(self):
        return {"status":self.status,"context":self.context,"input":self.input,
                "output":self.output,"identities":self.identities,
                "witnesses":[[key,str(value)] for key,value in self.witnesses],
                "anchor":None if self.anchor is None else [[str(v) for v in row] for row in self.anchor],
                "scope":self.scope}


class RelationalEngine:
    def __init__(self):
        self._sources={}
        self._contexts={}
        self._order=[]

    def observe(self,raw,source_id):
        if not isinstance(source_id,str) or not source_id.strip():
            raise ValueError("Source ID is required")
        encode(source_id)
        if source_id in self._sources:
            old=self._sources[source_id]
            if old.raw!=raw:
                raise ValueError("Source ID cannot change its observation")
            return old
        context,x,y,ids=parse(raw)  # No state mutation before complete validation.
        field=observation_field(source_id,x,y)
        bands=self._contexts.get(context)
        if bands is None:
            bands=Bands()
        start=bands.clock
        bands.feed(ids,field)
        measurement=Measurement(source_id,raw,context,x,y,start,bands.clock)
        self._contexts[context]=bands
        self._sources[source_id]=measurement
        self._order.append(source_id)
        return measurement

    def measurements(self):
        return tuple(self._sources[key] for key in self._order)

    def events(self,context):
        for source in self.measurements():
            if source.context==context:
                for i,identity in enumerate(encode(source.raw),source.start):
                    yield Event(context,i,identity)

    def inspect(self,context):
        if context not in self._contexts:
            return {"phase":"EMPTY","omega":0,"xi":None,"bands":[],"event_count":0,"anchor":None}
        bands=self._contexts[context]
        field=bands.field()
        anchor=field.operator() if field.phase=="SOLID" else None
        anchor_data=None if anchor is None else [[str(v) for v in row] for row in anchor]
        return {"phase":field.phase,"omega":field.omega,"omega_crit":6,
                "xi":None if field.xi is None else str(field.xi),
                "bands":bands.inspect(),"event_count":bands.clock,"anchor":anchor_data,
                "anchor_digest":None if anchor is None else sha256(canonical(anchor_data).encode()).hexdigest(),
                "conflict_witnesses":[{"row":[str(v) for v in row.values],
                    "sources":[[key,str(value)] for key,value in row.witnesses]}
                    for row in field.rows if row.pivot>=6]}

    def diagnose_owner_removal(self,context,indices):
        if any(type(i) is not int or not 0<=i<16 for i in indices):
            raise ValueError("Invalid band index")
        field=self._contexts[context].field(frozenset(indices))
        return {"phase":field.phase,"omega":field.omega,
                "xi":None if field.xi is None else str(field.xi),
                "scope":"diagnostic_intervention_not_normal_resolution"}

    def resolve(self,context,query):
        x=point(query)
        if context not in self._contexts:
            return Answer("NO_PATH",context,x)
        field=self._contexts[context].field()
        if field.phase!="SOLID":
            return Answer("CONFLICT" if field.conflict else "INCOMPLETE",context,x)
        value,witnesses=field.apply(x)
        if any(v.denominator!=1 for v in value):
            return Answer("OUTSIDE_LATTICE",context,x)
        y=tuple(int(v) for v in value)
        answer=Answer("RESOLVED",context,x,y,encode(canonical(y)),witnesses,field.operator())
        if not self.verify(answer):
            raise RuntimeError("Resolution witness failed source recomputation")
        return answer

    def verify(self,answer):
        if not isinstance(answer,Answer) or answer.status!="RESOLVED" or answer.output is None:
            return False
        try:
            x,y=point(answer.input),point(answer.output)
            if answer.identities!=encode(canonical(y)):
                return False
            if len({key for key,_ in answer.witnesses})!=len(answer.witnesses):
                return False
            a=[Q(0)]*6
            b=[Q(0)]*5
            for key,weight in answer.witnesses:
                if not isinstance(weight,Q):
                    return False
                source=self._sources[key]
                if source.context!=answer.context:
                    return False
                for i,v in enumerate((*source.input,1)):
                    a[i]+=weight*v
                for i,v in enumerate(source.output):
                    b[i]+=weight*v
            if tuple(a)!=(*x,1) or tuple(b)!=y:
                return False
            field=self._contexts[answer.context].field()
            return field.phase=="SOLID" and answer.anchor==field.operator()
        except (KeyError,TypeError,ValueError):
            return False

    def save(self,path):
        payload={"contract":CONTRACT,"registry":REGISTRY_ID,
                 "sources":[{"source_id":m.source_id,"raw":m.raw} for m in self.measurements()]}
        envelope={"payload":payload,"sha256":sha256(canonical(payload).encode()).hexdigest()}
        path=Path(path)
        temp_name=None
        try:
            with tempfile.NamedTemporaryFile(mode="w",encoding="utf8",dir=path.parent,
                                             prefix=path.name+".",suffix=".tmp",delete=False) as handle:
                temp_name=handle.name
                json.dump(envelope,handle,ensure_ascii=True,indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name,path)
        finally:
            if temp_name is not None and Path(temp_name).exists():
                Path(temp_name).unlink()

    @classmethod
    def load(cls,path):
        envelope=json.loads(Path(path).read_text(encoding="utf8"),object_pairs_hook=unique_object)
        if not isinstance(envelope,dict) or set(envelope)!={"payload","sha256"}:
            raise ValueError("Invalid checkpoint envelope")
        payload=envelope["payload"]
        if sha256(canonical(payload).encode()).hexdigest()!=envelope["sha256"]:
            raise ValueError("Checkpoint checksum mismatch")
        if not isinstance(payload,dict) or set(payload)!={"contract","registry","sources"}:
            raise ValueError("Invalid checkpoint payload")
        if payload["contract"]!=CONTRACT or payload["registry"]!=REGISTRY_ID or not isinstance(payload["sources"],list):
            raise ValueError("Incompatible contract or registry")
        result=cls()
        for entry in payload["sources"]:
            if not isinstance(entry,dict) or set(entry)!={"source_id","raw"}:
                raise ValueError("Invalid source entry")
            if not isinstance(entry["source_id"],str) or entry["source_id"] in result._sources:
                raise ValueError("Repeated or invalid source ID in checkpoint")
            result.observe(entry["raw"],entry["source_id"])
        return result

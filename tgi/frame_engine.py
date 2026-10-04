"""End-to-end frame crystal candidate for the user's exact acceptance package.

Literal experience retention is the tested knowledge contract. Anchor addresses
are allocated after C/L agreement; no claim of free-language semantic discovery.
"""
from dataclasses import dataclass,asdict
from fractions import Fraction
from hashlib import sha256
import json,os,tempfile
from pathlib import Path
from types import MappingProxyType
from .identity import encode,decode,REGISTRY_ID
from .resonance import ResonanceFrame
from .spatial import Atom,SpatialBond,LatticeView,coordinate,resonance_force,traverse

REVISION="TGI-FRAME-CRYSTAL-V1"


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=True)


def unique_object(pairs):
    result={}
    for key,value in pairs:
        if key in result:
            raise ValueError("Duplicate key in frame checkpoint")
        result[key]=value
    return result


@dataclass(frozen=True)
class Receipt:
    source_id: str
    anchor: int
    origin: tuple[int,...]
    count: int
    c_counts: tuple[int,...]
    l_ownership: tuple[tuple[int,int,int],...]
    omega_min: Fraction
    xi_min: Fraction
    reused: bool

    def as_dict(self):
        obj=asdict(self)
        obj["omega_min"]=str(self.omega_min)
        obj["xi_min"]=str(self.xi_min)
        return obj


class FrameEngine:
    def __init__(self):
        self._atoms={}
        self._bonds={}
        self._origins={}
        self._contexts={}
        self._sources={}
        self._pending={}

    def begin(self,source_id):
        if not isinstance(source_id,str) or not source_id.strip():
            raise ValueError("Source ID is required")
        encode(source_id)
        if source_id in self._pending or source_id in self._sources:
            raise ValueError("Source ID is already registered")
        frame=ResonanceFrame(source_id)
        self._pending[source_id]=frame
        return frame

    def commit(self,frame):
        if not isinstance(frame,ResonanceFrame) or self._pending.get(frame.source_id) is not frame:
            raise ValueError("Frame is not owned by this engine")
        proof=frame.certify()
        reused=proof.identities in self._contexts
        frame_index=self._contexts.get(proof.identities,len(self._contexts))
        origin=coordinate(frame_index,0)
        atoms={}
        bonds={}
        for i,identity in enumerate(proof.identities):
            omega=Fraction(int(proof.local_support[i])+int(proof.long_support[i]),2)
            xi=omega  # Frame complete, unique occurrence layout, pending address fixed.
            if omega<1 or xi!=1:
                raise ValueError("Insufficient structural saturation")
            coord=coordinate(frame_index,i)
            if coord in atoms:
                raise ValueError("Occurrence coordinates must remain distinct")
            atoms[coord]=Atom(coord,identity,omega,xi,i==len(proof.identities)-1)
        for i in range(len(proof.identities)-1):
            left,right=atoms[coordinate(frame_index,i)],atoms[coordinate(frame_index,i+1)]
            bonds[left.coordinate]=(SpatialBond(left.coordinate,right.coordinate,resonance_force(left,right)),)
        if reused:
            for coord,atom in atoms.items():
                if self._atoms.get(coord)!=atom:
                    raise ValueError("Existing context no longer matches its crystal")
            for coord,edges in bonds.items():
                if self._bonds.get(coord)!=edges:
                    raise ValueError("Existing context bonding no longer matches")
        elif any(coord in self._atoms for coord in atoms):
            raise ValueError("Context address collision")
        receipt=Receipt(frame.source_id,origin[3],origin,len(proof.identities),proof.c_counts,
                        proof.l_ownership,min(a.omega for a in atoms.values()),
                        min(a.xi for a in atoms.values()),reused)
        # Publish only after every atom, bond, and ownership check passed.
        if not reused:
            self._atoms.update(atoms)
            self._bonds.update(bonds)
            self._origins[origin[3]]=origin
            self._contexts[proof.identities]=frame_index
        self._sources[frame.source_id]=(proof.identities,receipt)
        del self._pending[frame.source_id]
        frame._closed=True
        return receipt

    def abort(self,frame):
        if not isinstance(frame,ResonanceFrame) or self._pending.get(frame.source_id) is not frame:
            raise ValueError("Frame is not owned by this engine")
        del self._pending[frame.source_id]
        frame._closed=True

    def ingest(self,text,source_id):
        ids=encode(text)
        if not ids:
            raise ValueError("Empty experience is not admissible")
        if source_id in self._sources:
            previous,receipt=self._sources[source_id]
            if ids!=previous:
                raise ValueError("Source cannot be changed under the same ID")
            return receipt
        frame=self.begin(source_id)
        frame.feed(text)
        return self.commit(frame)

    def ingest_batch(self, experiences):
        """Atomically publish new frame deltas without copying historical atoms."""
        from collections import ChainMap

        class DeltaMap(ChainMap):
            def __len__(self):
                # Only the small delta is scanned; the base is unchanged while
                # this transaction owns its private staging engine.
                return len(self.maps[1])+sum(key not in self.maps[1] for key in self.maps[0])

        fields = ("_atoms", "_bonds", "_origins", "_contexts", "_sources", "_pending")
        staged = FrameEngine()
        for name in fields:
            setattr(staged, name, DeltaMap({}, getattr(self, name)))
        receipts = tuple(staged.ingest(text, source_id) for text, source_id in experiences)
        if staged._pending.maps[0]:
            raise RuntimeError("Unfinished transaction frames")
        for name in fields:
            getattr(self, name).update(getattr(staged, name).maps[0])
        return receipts

    def view(self):
        # Copies form a stable lattice-only snapshot without source text access.
        return LatticeView(MappingProxyType(dict(self._atoms)),MappingProxyType(dict(self._bonds)),
                           MappingProxyType(dict(self._origins)))

    def resolve(self,trigger,anchor,max_new=None):
        return traverse(self.view(),trigger,anchor,max_new)

    def receipts(self):
        return tuple(receipt for _,receipt in self._sources.values())

    def inspect(self):
        return {"revision":REVISION,"sources":len(self._sources),"contexts":len(self._contexts),
                "atoms":len(self._atoms),"bonds":sum(len(v) for v in self._bonds.values()),
                "anchors":sorted(self._origins),"pending_sources":sorted(self._pending),
                "scope":"exact_episode_retention_and_isolated_traversal"}

    def save(self,path):
        if self._pending:
            raise ValueError("Cannot checkpoint with unfinished frames")
        payload={"revision":REVISION,"registry":REGISTRY_ID,
                 "sources":[{"source_id":key,"text":decode(ids),"anchor":receipt.anchor}
                            for key,(ids,receipt) in self._sources.items()]}
        envelope={"payload":payload,"sha256":sha256(canonical(payload).encode()).hexdigest()}
        path=Path(path)
        temporary=None
        try:
            with tempfile.NamedTemporaryFile(mode="w",encoding="utf8",dir=path.parent,
                                             prefix=path.name+".",suffix=".tmp",delete=False) as handle:
                temporary=handle.name
                json.dump(envelope,handle,ensure_ascii=True,indent=2)
                handle.flush(); os.fsync(handle.fileno())
            os.replace(temporary,path)
        finally:
            if temporary is not None and Path(temporary).exists():
                Path(temporary).unlink()

    @classmethod
    def load(cls,path):
        obj=json.loads(Path(path).read_text(encoding="utf8"),object_pairs_hook=unique_object)
        if not isinstance(obj,dict) or set(obj)!={"payload","sha256"}:
            raise ValueError("Invalid checkpoint envelope")
        payload=obj["payload"]
        if sha256(canonical(payload).encode()).hexdigest()!=obj["sha256"]:
            raise ValueError("Checkpoint checksum mismatch")
        if not isinstance(payload,dict) or set(payload)!={"revision","registry","sources"}:
            raise ValueError("Invalid payload schema")
        if payload["revision"]!=REVISION or payload["registry"]!=REGISTRY_ID or not isinstance(payload["sources"],list):
            raise ValueError("Incompatible frame contract or registry")
        engine=cls()
        for row in payload["sources"]:
            if not isinstance(row,dict) or set(row)!={"source_id","text","anchor"}:
                raise ValueError("Invalid source schema")
            if not isinstance(row["source_id"],str) or row["source_id"] in engine._sources:
                raise ValueError("Duplicate or invalid source ID")
            if type(row["anchor"]) is not int:
                raise ValueError("Invalid anchor")
            receipt=engine.ingest(row["text"],row["source_id"])
            if receipt.anchor!=row["anchor"]:
                raise ValueError("Anchor allocation does not reproduce")
        return engine

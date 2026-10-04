"""Journaled integration of grounded facts and controlled interventions."""
import copy, json, os, tempfile
from hashlib import sha256
from pathlib import Path
from .grounding import EvidenceStore, GroundedRelations
from .interventions import InterventionRelations
from .frame_engine import canonical, unique_object
from .identity import REGISTRY_ID

REVISION = "TGI-GROUNDED-EXPERIENCE-V2"


class ExperienceEngine:
    def __init__(self):
        self.store = EvidenceStore()
        self.facts = GroundedRelations(self.store)
        self.causes = InterventionRelations(self.store)
        self.journal = []

    def apply(self, event):
        if not isinstance(event, dict) or set(event) != {"op", "data"} or not isinstance(event["data"], dict):
            raise ValueError("Event requires op and data")
        candidate = copy.deepcopy(self)
        operations = {"teach": candidate.facts.teach, "fact": candidate.facts.ingest, "trial": candidate.causes.observe}
        if event["op"] not in operations:
            raise ValueError("Unknown experience operation")
        result = operations[event["op"]](**event["data"])
        if event["op"] == "fact" and result["status"] != "RESOLVED":
            return result
        candidate.journal.append(copy.deepcopy(event))
        self.__dict__.update(candidate.__dict__)
        return result

    def save(self, path):
        payload = {"revision": REVISION, "registry": REGISTRY_ID, "journal": self.journal}
        obj = {"payload": payload, "sha256": sha256(canonical(payload).encode()).hexdigest()}
        path = Path(path)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf8", dir=path.parent,
                                             prefix=path.name+".", suffix=".tmp", delete=False) as handle:
                temporary = handle.name
                json.dump(obj, handle, ensure_ascii=True, indent=2)
                handle.flush(); os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if temporary and Path(temporary).exists():
                Path(temporary).unlink()

    @classmethod
    def load(cls, path, allow_legacy=False):
        obj = json.loads(Path(path).read_text(encoding="utf8"), object_pairs_hook=unique_object)
        if not isinstance(obj, dict) or set(obj) != {"payload", "sha256"}:
            raise ValueError("Invalid checkpoint envelope")
        payload = obj["payload"]
        if sha256(canonical(payload).encode()).hexdigest() != obj["sha256"]:
            raise ValueError("Checkpoint checksum mismatch")
        if not isinstance(payload, dict) or set(payload) != {"revision", "registry", "journal"}:
            raise ValueError("Invalid payload")
        revisions = {REVISION, "TGI-GROUNDED-EXPERIENCE-V1"} if allow_legacy else {REVISION}
        if payload["revision"] not in revisions or payload["registry"] != REGISTRY_ID or not isinstance(payload["journal"], list):
            raise ValueError("Incompatible grounded experience contract")
        engine = cls()
        for event in payload["journal"]:
            result = engine.apply(event)
            if event["op"] == "fact" and result["status"] != "RESOLVED":
                raise ValueError("Checkpoint assertion cannot be reconstructed")
        return engine

"""Append-only acquisition with unchanged historical frame receipts."""
from .organization import RawOrganization
from .identity import encode,decode
from .frame_engine import canonical


class AcquisitionStream(RawOrganization):
    def extend(self,source,frames):
        """Accept a complete new prefix; identical retries are no-ops."""
        if not isinstance(source,str) or not source.strip():raise ValueError('Source required')
        encode(source)
        if not isinstance(frames,(list,tuple)) or not frames:raise ValueError('Nonempty frames required')
        raw=tuple(map(encode,frames))
        if any(not f for f in raw):raise ValueError('Empty frame')
        previous,receipts=self.episodes[source]
        if len(raw)<len(previous) or raw[:len(previous)]!=previous:raise ValueError('Historical prefix changed')
        if not self._alive(source):raise ValueError('Broken historical evidence')
        if raw==previous:return
        added=self.frames.ingest_batch((decode(raw[i]),canonical([source,i])) for i in range(len(previous),len(raw)))
        self.episodes[source]=(raw,receipts+added)
        self._dirty=True

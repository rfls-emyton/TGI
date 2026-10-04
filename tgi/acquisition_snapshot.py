"""Immutable original frame evidence; explicitly cannot authorize knowledge."""
from types import MappingProxyType
from .organization import RawOrganization
from .organization_snapshot import _Frames
from .frame_engine import Receipt


class AcquisitionSnapshot(RawOrganization):
    _acquisition_only=True

    def __init__(self,engine):
        if not isinstance(engine,RawOrganization):raise TypeError('Original acquisition model required')
        if getattr(engine.frames,'_pending',None):raise ValueError('Pending frame is not complete acquisition evidence')
        episodes=dict(engine.episodes)
        for value in episodes.values():
            if type(value) is not tuple or len(value)!=2 or type(value[0]) is not tuple or type(value[1]) is not tuple or any(type(f) is not tuple for f in value[0]) or any(type(r) is not Receipt for r in value[1]):raise ValueError('Immutable original episode/receipt containers required')
        self.frames=_Frames(engine.frames.view());self.episodes=MappingProxyType(episodes)
        self.organizations=MappingProxyType({});self.rejected_organizations=MappingProxyType({})
        self._dirty=True;self._valid={}

    def _alive(self,source):
        if source not in self._valid:self._valid[source]=super()._alive(source)
        return self._valid[source]

    def observe(self,*args,**kwargs):raise TypeError('Acquisition snapshot is read-only')
    def form(self,*args,**kwargs):raise TypeError('Acquisition snapshot cannot form knowledge')
    def resolve(self,*args,**kwargs):raise TypeError('Acquisition snapshot cannot resolve knowledge')
    def _phase_valid(self,*args,**kwargs):raise TypeError('Acquisition snapshot cannot admit knowledge phase')
    def save(self,*args,**kwargs):raise TypeError('Persist original model, not an acquisition-only snapshot')
    @classmethod
    def load(cls,*args,**kwargs):raise TypeError('Load original model, then snapshot acquisition')


def acquisition_snapshot(engine):
    return AcquisitionSnapshot(engine)

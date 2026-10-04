"""Immutable, call-scoped evidence snapshot; no cache survives a new snapshot."""
from types import MappingProxyType
from .organization import RawOrganization
from .spatial import traverse


class _Frames:
    def __init__(self, view):
        self._view = view

    def view(self):
        return self._view

    def resolve(self, trigger, anchor, max_new=None):
        return traverse(self._view, trigger, anchor, max_new)


class _Snapshot(RawOrganization):
    def __init__(self, engine):
        if getattr(engine,'_acquisition_only',False):
            raise TypeError('Acquisition evidence is not a formed knowledge snapshot')
        if engine._dirty:
            raise ValueError("Form organization before snapshot")
        self.frames = _Frames(engine.frames.view())
        self.episodes = MappingProxyType(dict(engine.episodes))
        self.organizations = MappingProxyType(dict(engine.organizations))
        self.rejected_organizations = MappingProxyType(dict(engine.rejected_organizations))
        self._dirty = False
        self._valid = {}
        self._phase = {}

    def _alive(self, source_id):
        if source_id not in self._valid:
            self._valid[source_id] = super()._alive(source_id)
        return self._valid[source_id]

    def _phase_valid(self, organization):
        if organization not in self._phase:
            self._phase[organization] = super()._phase_valid(organization)
        return self._phase[organization]

    def observe(self, *args, **kwargs):
        raise TypeError("Resolution snapshot is read-only")

    def form(self):
        raise TypeError("Resolution snapshot is read-only")


def snapshot(engine):
    return _Snapshot(engine)

"""Original-occurrence prefix organization for explicit complete episodes."""
from .organization import RawOrganization
from .organization_snapshot import snapshot


def project_roles(parent, *, max_search_steps=None):
    original = snapshot(parent)
    if not all(original._alive(source) for source in original.episodes):
        raise ValueError('Entire original evidence must remain valid')
    role = RawOrganization()
    role.frames = original.frames
    role.episodes = {source: (frames[:-1], receipts[:-1])
                     for source, (frames, receipts) in original.episodes.items()
                     if len(frames) >= 3}
    role.form(max_search_steps=max_search_steps)
    return role

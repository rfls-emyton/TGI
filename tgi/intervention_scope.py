"""Neutral decoding of scoped inventory onto original immutable occurrences.

No formation, role derivation, output selection or truth validation occurs here.
Callers must independently verify the complete inventory before using it.
"""
from .organization import RawOrganization,Organization
from .phase_evidence import Opposition


def _tuple(value):
    if type(value) in (bool,float):raise ValueError('Inventory scalar types must be exact')
    return tuple(_tuple(x) for x in value) if isinstance(value,(list,tuple)) else value


def decode_scope(view,scope,inventory):
    local=RawOrganization();local.frames=view.frames;local.episodes={s:view.episodes[s] for s in scope}
    if set(inventory)!={'active','rejected'}:raise ValueError('Invalid scoped inventory')
    def organization(row):
        if set(row)!={'anchor','pattern','supports','diversity'}:raise ValueError('Invalid inventory organization')
        return Organization(row['anchor'],_tuple(row['pattern']),_tuple(row['supports']),_tuple(row['diversity']))
    for row in inventory['active']:
        h=organization(row)
        if h.anchor in local.organizations:raise ValueError('Invalid scoped inventory')
        local.organizations[h.anchor]=h
    for row in inventory['rejected']:
        if set(row)!={'organization','oppositions'}:raise ValueError('Invalid scoped inventory')
        h=organization(row['organization']);opposed=[]
        for o in row['oppositions']:
            if set(o)!={'source','observed','predicted','observed_path','first_divergences'}:raise ValueError('Invalid scoped inventory')
            opposed.append(Opposition(o['source'],*(_tuple(o[k]) for k in ('observed','predicted','observed_path','first_divergences'))))
        if h.anchor in local.rejected_organizations:raise ValueError('Invalid scoped inventory')
        local.rejected_organizations[h.anchor]=(h,tuple(opposed))
    local._dirty=False
    return local

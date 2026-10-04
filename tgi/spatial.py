"""Discrete occurrence layout, positive bonds, and lattice-only traversal."""
from dataclasses import dataclass
from fractions import Fraction
from math import sqrt,isfinite,isclose
from typing import Mapping
from .identity import encode,decode


@dataclass(frozen=True)
class Atom:
    coordinate: tuple[int,...]
    identity: int
    omega: Fraction
    xi: Fraction
    terminal: bool


@dataclass(frozen=True)
class SpatialBond:
    start: tuple[int,...]
    end: tuple[int,...]
    force: float


def coordinate(frame_index,position):
    return (2+position,1,0,3+5*frame_index,(5-3*frame_index)%11)


def resonance_force(a,b):
    square_distance=sum((x-y)**2 for x,y in zip(a.coordinate,b.coordinate))
    if square_distance==0:
        raise ValueError("Coincident nodes cannot form this forward bond")
    norm_a=sum(x*x for x in a.coordinate)
    norm_b=sum(x*x for x in b.coordinate)
    if not norm_a or not norm_b:
        raise ValueError("Undefined angle")
    cosine=sum(x*y for x,y in zip(a.coordinate,b.coordinate))/sqrt(norm_a*norm_b)
    value=float(a.xi*b.xi)*cosine/square_distance
    if not isfinite(value) or value<=0:
        raise ValueError("Bond must have finite positive resonance force")
    return value


@dataclass(frozen=True)
class LatticeView:
    atoms: Mapping
    bonds: Mapping
    origins: Mapping


@dataclass(frozen=True)
class TraversalResult:
    status: str
    text: str | None = None
    identities: tuple[int,...] = ()
    path: tuple[tuple[int,...],...] = ()
    reason: str = ""


def traverse(view,trigger,anchor,max_new=None):
    identities=encode(trigger)
    if len(identities)!=1:
        raise ValueError("Trigger must be exactly one NMU character")
    if type(anchor) is not int:
        raise TypeError("Anchor must be an integer address")
    if max_new is not None and (type(max_new) is not int or max_new<0):
        raise ValueError("Safety ceiling must be a nonnegative integer")
    current=view.origins.get(anchor)
    atom=view.atoms.get(current)
    if atom is None or atom.identity!=identities[0]:
        return TraversalResult("NO_PATH",reason="Trigger coordinate is not crystallized")
    lane=current[3:]
    output=[]
    visited=[]
    ceiling=len(view.atoms)+1 if max_new is None else max_new
    while len(output)<ceiling:
        atom=view.atoms.get(current)
        if atom is None or atom.coordinate!=current or current[3:]!=lane or atom.omega<1 or atom.xi!=1:
            return TraversalResult("INCOMPLETE",reason="Missing or unlocked atom")
        if current in visited:
            return TraversalResult("INCOMPLETE",reason="Cycle violates forward momentum")
        visited.append(current)
        output.append(atom.identity)
        if atom.terminal:
            return TraversalResult("RESOLVED",decode(output),tuple(output),tuple(visited),"Explicit END reached")
        choices={}
        for bond in view.bonds.get(current,()):
            if bond.start!=current or bond.end[3:]!=lane:
                continue
            if tuple(y-x for x,y in zip(current,bond.end))!=(1,0,0,0,0):
                continue
            target=view.atoms.get(bond.end)
            if target is None or target.omega<1 or target.xi!=1:
                continue
            try:
                expected=resonance_force(atom,target)
            except (ValueError,OverflowError):
                continue
            if not isfinite(bond.force) or not isclose(bond.force,expected,rel_tol=1e-12,abs_tol=0):
                continue
            choices[bond.end]=bond.force
        if not choices:
            return TraversalResult("INCOMPLETE",reason="No supported forward bond")
        strongest=max(choices.values())
        best=[coord for coord,force in choices.items() if force==strongest]
        if len(best)!=1:
            return TraversalResult("AMBIGUOUS",reason="No unique geometric continuation")
        current=best[0]
    return TraversalResult("INCOMPLETE",reason="Safety ceiling reached before END")

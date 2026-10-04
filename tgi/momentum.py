"""Exact relative-angle operator; branch formation/admission is separate.

See contracts/RELATIVE_MOMENTUM_V1.md. This does not replace frame traversal.
"""
from dataclasses import dataclass
from fractions import Fraction


def _coordinate(value):
    if not isinstance(value,tuple) or len(value)!=5 or any(type(x) is not int for x in value):
        raise ValueError('Momentum coordinates must be tuples of five integers')
    return value


@dataclass(frozen=True)
class MomentumDecision:
    status: str
    target: tuple | None
    momentum: tuple
    scores: tuple
    rejected: tuple


def select_relative_momentum(previous, current, targets):
    previous,current=_coordinate(previous),_coordinate(current)
    candidates=sorted({_coordinate(t) for t in targets})
    momentum=tuple(a-p for p,a in zip(previous,current))
    if not any(momentum):
        return MomentumDecision('INCOMPLETE',None,momentum,(),tuple(candidates))
    scores=[];rejected=[]
    for target in candidates:
        delta=tuple(b-a for a,b in zip(current,target))
        dot=sum(m*d for m,d in zip(momentum,delta))
        if dot<=0:
            rejected.append(target);continue
        norm=sum(d*d for d in delta)
        scores.append((target,Fraction(dot*dot,norm)))
    if not scores:
        return MomentumDecision('NO_PATH',None,momentum,(),tuple(rejected))
    maximum=max(score for _,score in scores)
    best=[target for target,score in scores if score==maximum]
    return MomentumDecision('RESOLVED' if len(best)==1 else 'AMBIGUOUS',
        best[0] if len(best)==1 else None,momentum,tuple(scores),tuple(rejected))

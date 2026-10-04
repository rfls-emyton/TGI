"""Frame-scoped C/L structural resonance for the user acceptance contract.

C owns adjacency checks; L owns disjoint temporal blocks. This is exact
character evidence, not a semantic similarity or confidence estimator.
"""
from dataclasses import dataclass
from .events import Event,EventStream
from .identity import encode


@dataclass(frozen=True)
class TemporalBlock:
    start: int
    identities: tuple[int,...]

    @property
    def stop(self):
        return self.start+len(self.identities)


@dataclass(frozen=True)
class ResonanceProof:
    identities: tuple[int,...]
    local_support: tuple[bool,...]
    long_support: tuple[bool,...]
    c_counts: tuple[int,...]
    l_ownership: tuple[tuple[int,int,int],...]


class ResonanceFrame:
    def __init__(self,source_id):
        self.source_id=source_id
        self._stream=EventStream(source_id)
        self._events=[]
        self._c=[[] for _ in range(8)]
        self._l=[None]*8
        self._closed=False

    def feed(self,text):
        if self._closed:
            raise ValueError("A committed frame is immutable")
        encode(text)  # Reject entire invalid chunk before advancing event clock.
        new=self._stream.feed(text)
        for event in new:
            if self._events:
                previous=self._events[-1]
                self._c[previous.position%8].append((previous,event))
            self._events.append(event)
            carry=TemporalBlock(event.position,(event.identity,))
            for owner in range(8):
                old=self._l[owner]
                if old is None:
                    self._l[owner]=carry
                    break
                if old.stop!=carry.start:
                    raise RuntimeError("Broken temporal owner continuity")
                carry=TemporalBlock(old.start,old.identities+carry.identities)
                if owner==7:
                    self._l[owner]=carry
                    break
                self._l[owner]=None
        return new

    @property
    def events(self):
        return tuple(self._events)

    def certify(self):
        if not self._events:
            raise ValueError("Empty experience has no trigger atom")
        expected=tuple(e.identity for e in self._events)
        count=len(expected)
        edges=[]
        for owner,bank in enumerate(self._c):
            for left,right in bank:
                if left.position%8!=owner or right.position!=left.position+1:
                    raise ValueError("Invalid C ownership or adjacency")
                if left.stream_id!=self.source_id or right.stream_id!=self.source_id:
                    raise ValueError("Cross-stream local evidence")
                edges.append((left,right))
        edges.sort(key=lambda edge:edge[0].position)
        if len(edges)!=count-1:
            raise ValueError("Incomplete C adjacency support")
        reconstructed=[self._events[0].identity]
        for position,(left,right) in enumerate(edges):
            if left!=self._events[position] or right!=self._events[position+1]:
                raise ValueError("C evidence disagrees with received events")
            reconstructed.append(right.identity)
        long_ids=[]
        owners=[]
        ordered=sorted(((i,b) for i,b in enumerate(self._l) if b is not None),key=lambda item:item[1].start)
        for owner,block in ordered:
            if block.start!=len(long_ids):
                raise ValueError("Gap or overlap in L ownership")
            long_ids.extend(block.identities)
            owners.append((owner,block.start,block.stop))
        if tuple(reconstructed)!=expected or tuple(long_ids)!=expected:
            raise ValueError("Local and temporal resonance do not agree")
        # START and explicit END provide support for the two outer boundaries.
        return ResonanceProof(expected,(True,)*count,(True,)*count,
                              tuple(len(bank) for bank in self._c),tuple(owners))


def expected_ownership(count):
    """Closed-form C/L receipt layout, independently of the streaming producer."""
    if type(count) is not int or count<1:
        raise ValueError("Ownership count must be a positive integer")
    c_counts=tuple((count+6-owner)//8 for owner in range(8))
    blocks=[];cursor=0
    for owner in range(7,-1,-1):
        length=(count//128)*128 if owner==7 else (1<<owner if count & (1<<owner) else 0)
        if length:
            blocks.append((owner,cursor,cursor+length));cursor+=length
    return c_counts,tuple(blocks)

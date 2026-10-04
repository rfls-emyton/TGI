"""8 C + 8 L disjoint ownership of character-clock constraint blocks.

This is the declared TGI candidate, not a copy of the VEYRA MULTIPITA cell.
"""
from dataclasses import dataclass
from .exact_field import Field


@dataclass(frozen=True)
class Block:
    start: int
    stop: int
    field: Field


class Bands:
    def __init__(self):
        self.clock = 0
        self._banks = [None]*16
        self.merges = [0]*16

    def tick(self, field=Field()):
        carry = Block(self.clock,self.clock+1,field)
        self.clock += 1
        for index in range(16):
            old = self._banks[index]
            if old is None:
                self._banks[index] = carry
                return
            if old.stop != carry.start:
                raise RuntimeError("Noncontiguous band ownership")
            carry = Block(old.start,carry.stop,old.field.merge(carry.field))
            self.merges[index] += 1
            if index == 15:
                self._banks[index] = carry
                return
            self._banks[index] = None

    def feed(self, identities, final_field):
        if not identities:
            raise ValueError("A measurement frame must have character events")
        for i in range(len(identities)):
            self.tick(final_field if i == len(identities)-1 else Field())

    def field(self, excluded=()):
        result = Field()
        for i,block in enumerate(self._banks):
            if block is not None and i not in excluded:
                result = result.merge(block.field)
        return result

    def blocks(self):
        return tuple((i,block) for i,block in enumerate(self._banks) if block is not None)

    def inspect(self):
        return [{"owner":("C"+str(i)) if i<8 else ("L"+str(i-8)),
                 "index":i,"start":b.start,"stop":b.stop,
                 "rows":len(b.field.rows),"omega":b.field.omega,"phase":b.field.phase}
                for i,b in self.blocks()]

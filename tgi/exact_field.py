"""Exact affine-constraint algebra, a neutral implementation tool.

No optimizer, loss, floating-point embedding, or learned segmentation is used.
"""
from dataclasses import dataclass
from fractions import Fraction as Q


def weights_add(left, right, scale=Q(1)):
    values = dict(left)
    for key, value in right:
        values[key] = values.get(key, Q(0)) + scale * value
    return tuple(sorted((key, value) for key, value in values.items() if value))


@dataclass(frozen=True)
class Row:
    values: tuple[Q, ...]
    witnesses: tuple[tuple[str, Q], ...]

    @property
    def pivot(self):
        return next((i for i, value in enumerate(self.values) if value), None)

    def subtract(self, other, scale):
        return Row(tuple(a-scale*b for a,b in zip(self.values,other.values)),
                   weights_add(self.witnesses,other.witnesses,-scale))

    def normalized(self):
        pivot = self.pivot
        if pivot is None:
            return self
        scale = self.values[pivot]
        return Row(tuple(x/scale for x in self.values),tuple((k,v/scale) for k,v in self.witnesses))


@dataclass(frozen=True)
class Field:
    rows: tuple[Row, ...] = ()

    def insert(self, row):
        if len(row.values) != 11:
            raise ValueError("Expected five coordinates, affine offset, five consequences")
        for old in self.rows:
            if row.values[old.pivot]:
                row = row.subtract(old,row.values[old.pivot])
        if row.pivot is None:
            return self
        row = row.normalized()
        result = [old.subtract(row,old.values[row.pivot]) if old.values[row.pivot] else old
                  for old in self.rows]
        result.append(row)
        return Field(tuple(sorted(result,key=lambda item:item.pivot)))

    def merge(self, other):
        if not other.rows:
            return self
        if not self.rows:
            return other
        result = self
        for row in other.rows:
            result = result.insert(row)
        return result

    @property
    def omega(self):
        return sum(row.pivot < 6 for row in self.rows)

    @property
    def conflict(self):
        return any(row.pivot >= 6 for row in self.rows)

    @property
    def phase(self):
        if not self.rows:
            return "EMPTY"
        if self.conflict:
            return "CONFLICT"
        return "SOLID" if self.omega == 6 else "FLUID"

    @property
    def xi(self):
        return None if not self.rows else Q(0) if self.conflict else Q(self.omega,6)

    def operator(self):
        if self.phase != "SOLID":
            raise ValueError("Operator is not fully identified")
        return tuple(row.values[6:] for row in self.rows)

    def apply(self, point):
        operator = self.operator()
        a = (*point,1)
        value = tuple(sum((Q(a[i])*operator[i][j] for i in range(6)),Q(0)) for j in range(5))
        witnesses = ()
        for coefficient,row in zip(a,self.rows):
            witnesses = weights_add(witnesses,row.witnesses,Q(coefficient))
        return value,witnesses


def observation_field(source_id, point, consequence):
    return Field().insert(Row(tuple(Q(x) for x in (*point,1,*consequence)),((source_id,Q(1)),)))

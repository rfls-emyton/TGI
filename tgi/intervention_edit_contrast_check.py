"""Independent enumeration of all one-NMU alignments from original sequences."""
from tgi.identity import decode


def verify(row):
    try:
        if type(row) is not dict or set(row) != {
                'before_nmu', 'after_nmu', 'kind', 'positions', 'changed'}:
            return False
        a, b = row['before_nmu'], row['after_nmu']
        if type(a) is not list or type(b) is not list or not a or not b:
            return False
        decode(a)
        decode(b)
        if len(a) == len(b):
            mismatches = [i for i in range(len(a)) if a[i] != b[i]]
            if len(mismatches) > 1:
                return False
            kind = 'SUBSTITUTE' if mismatches else 'STABLE'
            positions = mismatches
        elif len(b) == len(a) + 1:
            positions = []
            for offset in range(len(b)):
                if all(a[j] == b[j if j < offset else j + 1]
                       for j in range(len(a))):
                    positions.append(offset)
            kind = 'INSERT'
        elif len(a) == len(b) + 1:
            positions = []
            for offset in range(len(a)):
                if all(b[j] == a[j if j < offset else j + 1]
                       for j in range(len(b))):
                    positions.append(offset)
            kind = 'DELETE'
        else:
            return False
        return bool(positions or kind == 'STABLE') and type(row['changed']) is bool and \
            row['kind'] == kind and row['positions'] == positions and \
            row['changed'] == (kind != 'STABLE')
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        return False

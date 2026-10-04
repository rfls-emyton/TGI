"""Single-occurrence NMU contrast; retains every valid edit alignment."""
from tgi.identity import encode


def contrast(before, after):
    if type(before) is not str or type(after) is not str or not before or not after:
        raise ValueError('Nonempty original raw frames required')
    left, right = list(encode(before)), list(encode(after))
    if len(left) == len(right):
        positions = [i for i, (a, b) in enumerate(zip(left, right)) if a != b]
        if len(positions) > 1:
            raise ValueError('More than one changed NMU occurrence')
        kind = 'SUBSTITUTE' if positions else 'STABLE'
    elif len(right) == len(left) + 1:
        positions = [i for i in range(len(right)) if right[:i] + right[i + 1:] == left]
        if not positions:
            raise ValueError('Not a single NMU insertion')
        kind = 'INSERT'
    elif len(left) == len(right) + 1:
        positions = [i for i in range(len(left)) if left[:i] + left[i + 1:] == right]
        if not positions:
            raise ValueError('Not a single NMU deletion')
        kind = 'DELETE'
    else:
        raise ValueError('More than one changed NMU occurrence')
    return {'before_nmu': left, 'after_nmu': right, 'kind': kind,
            'positions': positions, 'changed': kind != 'STABLE'}

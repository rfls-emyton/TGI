"""Independent raw-NMU validation and exhaustive incidence-class replay."""
from .identity import decode, encode
from .causal_port_classes_check import verify as replay

REVISION = 'TGI-M1-RESPONSE-INCIDENCE-V1'


def valid_response(row):
    try:
        if type(row) is not dict or set(row) != {'before_nmu', 'after_nmu', 'kind', 'changed'} or \
                type(row['before_nmu']) is not list or type(row['after_nmu']) is not list or \
                not row['before_nmu'] or not row['after_nmu'] or type(row['changed']) is not bool:
            return False
        before = decode(row['before_nmu'])
        after = decode(row['after_nmu'])
        if list(encode(before)) != row['before_nmu'] or list(encode(after)) != row['after_nmu']:
            return False
        changed = row['before_nmu'] != row['after_nmu']
        return row['changed'] == changed and row['kind'] == ('CHANGED' if changed else 'STABLE')
    except (ValueError, TypeError, KeyError):
        return False


def verify(events, certificate):
    return replay(events, certificate, revision=REVISION, valid_row=valid_response)

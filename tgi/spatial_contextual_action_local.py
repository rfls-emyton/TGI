"""Derive one changed contextual family from a locally updated direct certificate."""
from itertools import combinations

from .frame_engine import canonical
from .organization import OMEGA_CRIT


def family_from_relation(relation):
    witnesses = relation['witnesses']
    lengths = {len(row['before_nmu']) for row in witnesses}
    ports = {row['port'] for row in witnesses}
    if len(lengths) != 1 or len(ports) != 1:
        raise ValueError('One observed length and port family required')
    length, port = next(iter(lengths)), next(iter(ports))
    positions = tuple(index for index in range(length) if index != port)
    conflicting = len({row['output_nmu'] for row in witnesses}) > 1
    by_before = {}
    for row in witnesses:
        before = tuple(row['before_nmu'])
        if before in by_before and by_before[before] != row['output_nmu']:
            return {'anchor': relation['anchor'], 'length': length, 'port': port,
                    'separator': None, 'cells': [],
                    'status': 'UNSEPARATED_CONFLICT'}
        by_before[before] = row['output_nmu']
    separator = None
    for size in range(len(positions) + 1):
        for selected in combinations(positions, size):
            outputs_by_key = {}
            for row in witnesses:
                key = tuple(row['before_nmu'][index] for index in selected)
                output = row['output_nmu']
                if key in outputs_by_key and outputs_by_key[key] != output:
                    break
                outputs_by_key[key] = output
            else:
                separator = list(selected)
                break
        if separator is not None:
            break
    if separator is None:
        return {'anchor': relation['anchor'], 'length': length, 'port': port,
                'separator': None, 'cells': [], 'status': 'UNSEPARATED_CONFLICT'}
    cells = {}
    for row in witnesses:
        key = tuple(row['before_nmu'][index] for index in separator)
        cells.setdefault(key, []).append(row)
    rows = []
    for key, group in sorted(cells.items()):
        outputs = sorted({row['output_nmu'] for row in group})
        contexts = {canonical(row['context']) for row in group}
        omega = min(len(group), len(contexts))
        status = 'REVOKED' if len(outputs) > 1 else 'CRYSTAL' if omega >= OMEGA_CRIT else 'LIQUID'
        rows.append({'key_nmu': list(key), 'outputs_nmu': outputs,
                     'support_sources': [row['source'] for row in group],
                     'omega': omega, 'xi': int(status == 'CRYSTAL'),
                     'status': status})
    return {'anchor': relation['anchor'], 'length': length, 'port': port,
            'separator': separator, 'cells': rows,
            'status': 'CONTEXT_BOUNDARY' if conflicting else 'UNCONTESTED'}


def append_contextual_family(previous, direct, event):
    if (previous['direct_certificate']['source_count'] + 1 != direct['source_count'] or
            event['source'] not in {source for relation in direct['relations']
                                    for source in relation['support_sources']}):
        raise ValueError('Direct certificate is not a one-source extension')
    changed = (tuple(event['action_nmu']), event['input_nmu'])
    old = {row['anchor']: row for row in previous['families']}
    families = []
    for relation in direct['relations']:
        key = (tuple(relation['action_nmu']), relation['input_nmu'])
        if key == changed:
            families.append(family_from_relation(relation))
        else:
            family = old.get(relation['anchor'])
            if family is None:
                raise ValueError('Unchanged family missing')
            families.append(family)
    return {**previous, 'direct_certificate': direct, 'families': families}

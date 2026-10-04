"""Runtime: exact NMU occurrence boundary between conflicting action outputs.

All historical witnesses remain present.  A conditional crystal is available
only when observed stable positions separate every opposing-output pair.
"""
from itertools import combinations

from .frame_engine import canonical
from .organization import OMEGA_CRIT
from .spatial_direct_action_relation import form_direct_raw_relations
from .spatial_direct_action_relation_check import verify_direct_raw_relation


def form_contextual_phase(model, commands):
    direct = form_direct_raw_relations(model, commands)
    if not verify_direct_raw_relation(model, commands, direct):
        raise ValueError('Raw relation phase verification failed')
    families = []
    for relation in direct['relations']:
        witnesses = relation['witnesses']
        lengths = {len(row['before_nmu']) for row in witnesses}
        ports = {row['port'] for row in witnesses}
        if len(lengths) != 1 or len(ports) != 1:
            raise ValueError('One observed length and port family required')
        length, port = next(iter(lengths)), next(iter(ports))
        stable_positions = tuple(index for index in range(length) if index != port)
        conflicts = [(left, right) for left in range(len(witnesses))
                     for right in range(left + 1, len(witnesses))
                     if witnesses[left]['output_nmu'] != witnesses[right]['output_nmu']]
        separator = None
        impossible = any(witnesses[i]['before_nmu'] == witnesses[j]['before_nmu']
                         for i, j in conflicts)
        if not impossible:
            for size in range(len(stable_positions) + 1):
                for positions in combinations(stable_positions, size):
                    if all(any(witnesses[i]['before_nmu'][position] !=
                               witnesses[j]['before_nmu'][position] for position in positions)
                           for i, j in conflicts):
                        separator = list(positions)
                        break
                if separator is not None:
                    break
        if separator is None:
            families.append({'anchor': relation['anchor'], 'length': length,
                             'port': port, 'separator': None, 'cells': [],
                             'status': 'UNSEPARATED_CONFLICT'})
            continue
        cells = {}
        for row in witnesses:
            key = tuple(row['before_nmu'][position] for position in separator)
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
        families.append({'anchor': relation['anchor'], 'length': length,
                         'port': port, 'separator': separator, 'cells': rows,
                         'status': 'CONTEXT_BOUNDARY' if conflicts else 'UNCONTESTED'})
    return {'policy': 's2_observed_context_boundary_v1', 'threshold': OMEGA_CRIT,
            'direct_certificate': direct, 'families': families}


def resolve_contextual_phase(certificate, anchor, before_nmu):
    family = next((row for row in certificate['families'] if row['anchor'] == anchor), None)
    relation = next((row for row in certificate['direct_certificate']['relations']
                     if row['anchor'] == anchor), None)
    if (family is None or relation is None or family['separator'] is None or
            len(before_nmu) != family['length'] or
            before_nmu[family['port']] != relation['input_nmu']):
        return {'status': 'NO_PATH', 'output_nmu': None}
    key = [before_nmu[index] for index in family['separator']]
    cell = next((row for row in family['cells'] if row['key_nmu'] == key), None)
    if cell is None or cell['status'] != 'CRYSTAL':
        return {'status': 'NO_PATH', 'output_nmu': None}
    return {'status': 'CRYSTAL', 'output_nmu': cell['outputs_nmu'][0]}

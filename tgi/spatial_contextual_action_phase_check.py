"""Independent runtime witness-level checker for observed NMU context boundaries."""
from itertools import combinations

from .frame_engine import canonical
from .organization import OMEGA_CRIT
from .spatial_direct_action_relation_check import verify_direct_raw_relation


def verify_contextual_phase(model, commands, certificate):
    try:
        if (type(certificate) is not dict or
                set(certificate) != {'policy', 'threshold', 'direct_certificate', 'families'} or
                certificate['policy'] != 's2_observed_context_boundary_v1' or
                certificate['threshold'] != OMEGA_CRIT or
                not verify_direct_raw_relation(model, commands, certificate['direct_certificate'])):
            return False
        direct = certificate['direct_certificate']['relations']
        if type(certificate['families']) is not list or len(certificate['families']) != len(direct):
            return False
        for relation, family in zip(direct, certificate['families']):
            witnesses = relation['witnesses']
            if type(family) is not dict or set(family) != {'anchor', 'length', 'port', 'separator', 'cells', 'status'}:
                return False
            lengths = {len(row['before_nmu']) for row in witnesses}
            ports = {row['port'] for row in witnesses}
            if len(lengths) != 1 or len(ports) != 1:
                return False
            length, port = next(iter(lengths)), next(iter(ports))
            if family['anchor'] != relation['anchor'] or family['length'] != length or family['port'] != port:
                return False
            disagreements = [(a, b) for a in range(len(witnesses))
                             for b in range(a + 1, len(witnesses))
                             if witnesses[a]['output_nmu'] != witnesses[b]['output_nmu']]
            available = [i for i in range(length) if i != port]
            first = None
            impossible = any(witnesses[a]['before_nmu'] == witnesses[b]['before_nmu']
                             for a, b in disagreements)
            if not impossible:
                for count in range(len(available) + 1):
                    for selected in combinations(available, count):
                        valid = True
                        for a, b in disagreements:
                            if not any(witnesses[a]['before_nmu'][i] != witnesses[b]['before_nmu'][i]
                                       for i in selected):
                                valid = False
                                break
                        if valid:
                            first = list(selected)
                            break
                    if first is not None:
                        break
            if family['separator'] != first:
                return False
            if first is None:
                if family['cells'] or family['status'] != 'UNSEPARATED_CONFLICT':
                    return False
                continue
            expected = {}
            for row in witnesses:
                key = tuple(row['before_nmu'][i] for i in first)
                expected.setdefault(key, []).append(row)
            if family['status'] != ('CONTEXT_BOUNDARY' if disagreements else 'UNCONTESTED'):
                return False
            rows = family['cells']
            if type(rows) is not list or len(rows) != len(expected):
                return False
            for row, (key, group) in zip(rows, sorted(expected.items())):
                if type(row) is not dict or set(row) != {'key_nmu', 'outputs_nmu', 'support_sources', 'omega', 'xi', 'status'}:
                    return False
                outputs = sorted({item['output_nmu'] for item in group})
                contexts = {canonical(item['context']) for item in group}
                omega = min(len(group), len(contexts))
                status = 'REVOKED' if len(outputs) > 1 else 'CRYSTAL' if omega >= OMEGA_CRIT else 'LIQUID'
                if (row['key_nmu'] != list(key) or row['outputs_nmu'] != outputs or
                        row['support_sources'] != [item['source'] for item in group] or
                        row['omega'] != omega or row['xi'] != int(status == 'CRYSTAL') or
                        row['status'] != status):
                    return False
        return True
    except (AttributeError, IndexError, KeyError, TypeError, ValueError):
        return False

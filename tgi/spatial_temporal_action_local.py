"""Local temporal phase transition over one newly verified raw relation event."""
from .frame_engine import canonical
from .organization import OMEGA_CRIT
from .spatial_contextual_action_local import family_from_relation


def _family(relation, spatial_family, order):
    witnesses = sorted(relation['witnesses'], key=lambda row: order[row['source']])
    seen = {}
    trigger = None
    for index, row in enumerate(witnesses):
        key = tuple(row['before_nmu'])
        if key in seen and seen[key] != row['output_nmu']:
            trigger = index
            break
        seen[key] = row['output_nmu']
    if trigger is None:
        return {'anchor': relation['anchor'], 'mode': 'SPATIAL',
                'spatial_family': spatial_family, 'separator': None, 'cells': []}
    baseline = family_from_relation({**relation, 'witnesses': witnesses[:trigger]})
    separator = baseline['separator']
    if separator is None:
        raise ValueError('Pre-trigger spatial baseline unresolved')
    groups = {}
    for row in witnesses:
        key = tuple(row['before_nmu'][position] for position in separator)
        groups.setdefault(key, []).append(row)
    cells = []
    for key, rows in sorted(groups.items()):
        epochs = []
        for row in rows:
            if not epochs or epochs[-1]['output_nmu'] != row['output_nmu']:
                old = [item for epoch in epochs for item in epoch['witnesses']]
                proven = not epochs or any(
                    item['before_nmu'] == row['before_nmu'] and
                    item['output_nmu'] != row['output_nmu'] for item in old)
                epochs.append({'output_nmu': row['output_nmu'],
                               'proven_transition': proven, 'witnesses': []})
            epochs[-1]['witnesses'].append(row)
        records = []
        for epoch in epochs:
            group = epoch['witnesses']
            omega = min(len(group), len({canonical(item['context']) for item in group}))
            phase = ('CRYSTAL' if epoch['proven_transition'] and omega >= OMEGA_CRIT
                     else 'LIQUID')
            records.append({'output_nmu': epoch['output_nmu'],
                            'source_ids': [item['source'] for item in group],
                            'omega': omega, 'xi': int(phase == 'CRYSTAL'),
                            'proven_transition': epoch['proven_transition'],
                            'status': phase})
        cells.append({'key_nmu': list(key), 'epochs': records})
    return {'anchor': relation['anchor'], 'mode': 'TEMPORAL',
            'spatial_family': spatial_family, 'separator': separator,
            'cells': cells}


def append_temporal_phase(previous, new_spatial, event, commands):
    prior = previous['spatial_certificate']['direct_certificate']
    direct = new_spatial['direct_certificate']
    if (prior['source_count'] + 1 != direct['source_count'] or
            commands[-1]['source'] != event['source']):
        raise ValueError('One chronological raw event required')
    order = {row['source']: index for index, row in enumerate(commands)}
    changed = (tuple(event['action_nmu']), event['input_nmu'])
    old = {row['anchor']: row for row in previous['families']}
    families = []
    for relation, spatial_family in zip(direct['relations'], new_spatial['families']):
        key = (tuple(relation['action_nmu']), relation['input_nmu'])
        if key == changed:
            families.append(_family(relation, spatial_family, order))
        else:
            family = old.get(relation['anchor'])
            if family is None:
                raise ValueError('Unchanged temporal family missing')
            families.append(family)
    return {**previous, 'spatial_certificate': new_spatial,
            'families': families}

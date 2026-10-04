"""Research: append-only temporal validity after repeated raw pre-state conflict."""
from .frame_engine import canonical
from .organization import OMEGA_CRIT
from .spatial_contextual_action_phase import form_contextual_phase
from .spatial_contextual_action_local import family_from_relation


def _no_path():
    return {'status': 'NO_PATH', 'output_nmu': None}


def form_temporal_phase(model, commands):
    if [row['source'] for row in commands] != list(model.episodes):
        raise ValueError('Temporal commands must follow raw episode order')
    spatial = form_contextual_phase(model, commands)
    order = {row['source']: index for index, row in enumerate(commands)}
    families = []
    for relation, spatial_family in zip(spatial['direct_certificate']['relations'],
                                        spatial['families']):
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
            families.append({'anchor': relation['anchor'], 'mode': 'SPATIAL',
                             'spatial_family': spatial_family, 'separator': None,
                             'cells': []})
            continue
        baseline = family_from_relation({**relation, 'witnesses': witnesses[:trigger]})
        if baseline['separator'] is None:
            raise ValueError('Pre-trigger spatial baseline unresolved')
        separator = baseline['separator']
        cells = {}
        for row in witnesses:
            key = tuple(row['before_nmu'][position] for position in separator)
            runs = cells.setdefault(key, [])
            output = row['output_nmu']
            if not runs or runs[-1]['output_nmu'] != output:
                prior = [item for run in runs for item in run['witnesses']]
                proven = not runs or any(
                    item['before_nmu'] == row['before_nmu'] and
                    item['output_nmu'] != output for item in prior)
                runs.append({'output_nmu': output, 'proven_transition': proven,
                             'witnesses': []})
            runs[-1]['witnesses'].append(row)
        rows = []
        for key, runs in sorted(cells.items()):
            epochs = []
            for run in runs:
                group = run['witnesses']
                omega = min(len(group), len({canonical(item['context']) for item in group}))
                status = 'CRYSTAL' if omega >= OMEGA_CRIT and run['proven_transition'] else 'LIQUID'
                epochs.append({'output_nmu': run['output_nmu'],
                               'source_ids': [item['source'] for item in group],
                               'omega': omega, 'xi': int(status == 'CRYSTAL'),
                               'proven_transition': run['proven_transition'],
                               'status': status})
            rows.append({'key_nmu': list(key), 'epochs': epochs})
        families.append({'anchor': relation['anchor'], 'mode': 'TEMPORAL',
                         'spatial_family': spatial_family,
                         'separator': separator, 'cells': rows})
    return {'policy': 's2_temporal_epoch_research_v1',
            'threshold': OMEGA_CRIT, 'spatial_certificate': spatial,
            'families': families}


def resolve_temporal_phase(certificate, anchor, before_nmu):
    spatial = certificate['spatial_certificate']
    relation = next((row for row in spatial['direct_certificate']['relations']
                     if row['anchor'] == anchor), None)
    family = next((row for row in certificate['families']
                   if row['anchor'] == anchor), None)
    if (relation is None or family is None or
            len(before_nmu) != family['spatial_family']['length'] or
            before_nmu[family['spatial_family']['port']] != relation['input_nmu']):
        return _no_path()
    if family['mode'] == 'SPATIAL':
        from .spatial_contextual_action_phase import resolve_contextual_phase
        return resolve_contextual_phase(spatial, anchor, before_nmu)
    key = [before_nmu[position] for position in family['separator']]
    cell = next((row for row in family['cells'] if row['key_nmu'] == key), None)
    if cell is None or not cell['epochs'] or cell['epochs'][-1]['status'] != 'CRYSTAL':
        return _no_path()
    return {'status': 'CRYSTAL', 'output_nmu': cell['epochs'][-1]['output_nmu']}

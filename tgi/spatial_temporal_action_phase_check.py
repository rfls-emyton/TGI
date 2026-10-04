"""Independent raw-witness checker for the research temporal phase certificate."""
from itertools import combinations

from .frame_engine import canonical
from .organization import OMEGA_CRIT, RawOrganization
from .spatial_contextual_action_phase_check import verify_contextual_phase


def verify_temporal_phase(model, commands, certificate):
    try:
        if (type(model) is not RawOrganization or type(commands) is not list or
                type(certificate) is not dict or
                set(certificate) != {'policy', 'threshold', 'spatial_certificate', 'families'} or
                certificate['policy'] != 's2_temporal_epoch_research_v1' or
                certificate['threshold'] != OMEGA_CRIT or
                [row['source'] for row in commands] != list(model.episodes) or
                not verify_contextual_phase(model, commands,
                                            certificate['spatial_certificate'])):
            return False
        spatial = certificate['spatial_certificate']
        relations = spatial['direct_certificate']['relations']
        if type(certificate['families']) is not list or len(certificate['families']) != len(relations):
            return False
        order = {row['source']: index for index, row in enumerate(commands)}
        expected = []
        for relation, spatial_family in zip(relations, spatial['families']):
            witnesses = sorted(relation['witnesses'], key=lambda row: order[row['source']])
            trigger = None
            earlier = {}
            for index, row in enumerate(witnesses):
                before = tuple(row['before_nmu'])
                if before in earlier and row['output_nmu'] != earlier[before]:
                    trigger = index
                    break
                earlier[before] = row['output_nmu']
            if trigger is None:
                expected.append({'anchor': relation['anchor'], 'mode': 'SPATIAL',
                                 'spatial_family': spatial_family,
                                 'separator': None, 'cells': []})
                continue
            prefix = witnesses[:trigger]
            length = len(prefix[0]['before_nmu'])
            port = prefix[0]['port']
            available = [i for i in range(length) if i != port]
            opposition = [(left, right) for left in range(len(prefix))
                          for right in range(left + 1, len(prefix))
                          if prefix[left]['output_nmu'] != prefix[right]['output_nmu']]
            separator = None
            for size in range(len(available) + 1):
                for selected in combinations(available, size):
                    if all(any(prefix[a]['before_nmu'][i] != prefix[b]['before_nmu'][i]
                               for i in selected) for a, b in opposition):
                        separator = list(selected)
                        break
                if separator is not None:
                    break
            if separator is None:
                return False
            buckets = {}
            for row in witnesses:
                key = tuple(row['before_nmu'][i] for i in separator)
                buckets.setdefault(key, []).append(row)
            cells = []
            for key, rows in sorted(buckets.items()):
                epochs = []
                run = []
                for row in rows:
                    if run and row['output_nmu'] != run[-1]['output_nmu']:
                        epochs.append(run)
                        run = []
                    run.append(row)
                if run:
                    epochs.append(run)
                records = []
                previous = []
                for index, epoch in enumerate(epochs):
                    first = epoch[0]
                    proven = index == 0 or any(
                        item['before_nmu'] == first['before_nmu'] and
                        item['output_nmu'] != first['output_nmu'] for item in previous)
                    omega = min(len(epoch), len({canonical(row['context']) for row in epoch}))
                    phase = 'CRYSTAL' if proven and omega >= OMEGA_CRIT else 'LIQUID'
                    records.append({'output_nmu': first['output_nmu'],
                                    'source_ids': [row['source'] for row in epoch],
                                    'omega': omega, 'xi': int(phase == 'CRYSTAL'),
                                    'proven_transition': proven, 'status': phase})
                    previous.extend(epoch)
                cells.append({'key_nmu': list(key), 'epochs': records})
            expected.append({'anchor': relation['anchor'], 'mode': 'TEMPORAL',
                             'spatial_family': spatial_family,
                             'separator': separator, 'cells': cells})
        return canonical(certificate['families']) == canonical(expected)
    except (AttributeError, IndexError, KeyError, TypeError, ValueError):
        return False

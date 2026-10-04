"""Independent full replay of local NMU edit transport classes."""
from tgi.frame_engine import canonical
from tgi.identity import REGISTRY_ID, decode
from tgi.organization import OMEGA_CRIT
from tgi.intervention_edit_contrast_check import verify as valid_contrast

REVISION = 'TGI-M1-LOCAL-EDIT-TRANSPORT-CLASSES-RESEARCH-V4'


def _changed_atom(row):
    if row['kind'] == 'STABLE':
        return ('STABLE',)
    if row['kind'] == 'SUBSTITUTE':
        if len(row['positions']) != 1:
            raise ValueError('Invalid substitution alignment')
        i = row['positions'][0]
        return ('SUBSTITUTE', row['before_nmu'][i], row['after_nmu'][i])
    source = row['after_nmu'] if row['kind'] == 'INSERT' else row['before_nmu']
    atoms = [source[i] for i in row['positions']]
    if not atoms or any(atom != atoms[0] for atom in atoms[1:]):
        raise ValueError('Ambiguous changed NMU identity')
    return (row['kind'], atoms[0])


def _measure(data, members, row, names):
    action = tuple(row['action_nmu'])
    stable = all(row['ports'][port]['kind'] == 'STABLE' for port in members)
    changed = all(row['ports'][port]['kind'] != 'STABLE' for port in members)
    if changed:
        key = tuple(tuple(row['ports'][port]['before_nmu']) for port in members)
        data['contexts'].setdefault(action, set()).add(key)
    if stable:
        data['controls'][action] = data['controls'].get(action, 0) + 1
        if any(row['ports'][port]['kind'] != 'STABLE' for port in names if port not in members):
            data['separators'].add(action)


def verify(events, certificate):
    try:
        if (type(events) is not list or type(certificate) is not dict or
                set(certificate) != {'revision', 'registry', 'events', 'phases', 'result'} or
                certificate['revision'] != REVISION or certificate['registry'] != REGISTRY_ID or
                canonical(certificate['events']) != canonical(events) or
                type(certificate['phases']) is not list or len(certificate['phases']) != len(events)):
            return False
        names = None
        seen = set()
        traces = {}
        actions = set()
        epoch_rows = []
        old_groups = {}
        prior_crystal = None
        epoch_start = 0
        result = {'status': 'NO_PATH', 'action_nmu': None, 'members': None}
        for index, event in enumerate(events):
            if (type(event) is not dict or set(event) != {'source', 'action_nmu', 'ports'} or
                    type(event['source']) is not str or not event['source'] or event['source'] in seen or
                    type(event['action_nmu']) is not list or not event['action_nmu'] or
                    type(event['ports']) is not dict):
                return False
            seen.add(event['source'])
            decode(event['action_nmu'])
            current_names = list(event['ports'])
            if (len(current_names) < 3 or current_names != sorted(current_names) or
                    any(type(name) is not str or not name for name in current_names)):
                return False
            if names is None:
                names = current_names
                traces = {name: [] for name in names}
            elif current_names != names:
                return False
            for name in names:
                contrast = event['ports'][name]
                if not valid_contrast(contrast):
                    return False
                traces[name].append(_changed_atom(contrast))
            epoch_rows.append(event)
            actions.add(tuple(event['action_nmu']))
            partition = {}
            for name in names:
                partition.setdefault(tuple(traces[name]), []).append(name)
            groups = sorted(tuple(members) for members in partition.values())
            new_groups = {}
            cells = []
            winners = []
            for members in groups:
                if members in old_groups:
                    data = old_groups[members]
                    _measure(data, members, event, names)
                else:
                    data = {'contexts': {}, 'controls': {}, 'separators': set()}
                    for row in epoch_rows:
                        _measure(data, members, row, names)
                new_groups[members] = data
                counts = []
                for action in sorted(actions):
                    omega = len(data['contexts'].get(action, ()))
                    controls = data['controls'].get(action, 0)
                    comparison = any(other != action for other in data['separators'])
                    counts.append({'action_nmu': list(action), 'omega': omega,
                                   'controls': controls, 'comparator': comparison})
                    if omega >= OMEGA_CRIT and controls and comparison:
                        winners.append((action, members))
                cells.append({'members': list(members), 'C_L_by_action': counts, 'xi': 0})
            if prior_crystal is not None and prior_crystal not in groups:
                result = {'status': 'REVOKED', 'action_nmu': None, 'members': None}
                prior_crystal = None
                epoch_start = index + 1
                epoch_rows = []
                new_groups = {}
            elif len(winners) == 1:
                action, members = winners[0]
                result = {'status': 'CRYSTAL', 'action_nmu': list(action), 'members': list(members)}
                prior_crystal = members
                for cell in cells:
                    cell['xi'] = int(tuple(cell['members']) == members)
            elif prior_crystal is not None and not any(members == prior_crystal for _, members in winners):
                result = {'status': 'REVOKED', 'action_nmu': None, 'members': None}
            else:
                result = {'status': 'NO_PATH', 'action_nmu': None, 'members': None}
            expected = {'event_index': index, 'source': event['source'],
                        'epoch_start': epoch_start, 'classes': cells, 'result': result}
            if canonical(certificate['phases'][index]) != canonical(expected):
                return False
            old_groups = new_groups
        return canonical(certificate['result']) == canonical(result)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        return False

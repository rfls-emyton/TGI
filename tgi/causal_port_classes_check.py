"""Independent exhaustive replay of observational edit-topology classes."""
from .frame_engine import canonical
from .identity import REGISTRY_ID, decode
from .intervention_edit_contrast_check import verify as valid_contrast
from .organization import OMEGA_CRIT

REVISION = 'TGI-M1-CAUSAL-PORT-TOPOLOGY-V1'


def verify(events, certificate, *, revision=REVISION, valid_row=valid_contrast):
    try:
        if type(events) is not list or type(certificate) is not dict or \
                set(certificate) != {'revision', 'registry', 'events', 'phases', 'result'} or \
                certificate['revision'] != revision or certificate['registry'] != REGISTRY_ID or \
                canonical(certificate['events']) != canonical(events) or \
                type(certificate['phases']) is not list or len(certificate['phases']) != len(events):
            return False
        names = None
        sources = set()
        prior = None
        epoch = 0
        final = {'status': 'NO_PATH', 'action_nmu': None, 'members': None}
        for stop, event in enumerate(events):
            if type(event) is not dict or set(event) != {'source', 'action_nmu', 'ports'} or \
                    type(event['source']) is not str or not event['source'] or event['source'] in sources or \
                    type(event['action_nmu']) is not list or not event['action_nmu'] or \
                    type(event['ports']) is not dict:
                return False
            sources.add(event['source'])
            if not decode(event['action_nmu']):
                return False
            observed = list(event['ports'])
            if len(observed) < 3 or observed != sorted(observed) or \
                    any(type(name) is not str or not name or not valid_row(event['ports'][name])
                        for name in observed):
                return False
            if names is None:
                names = observed
            if observed != names:
                return False
            prefix = events[:stop+1]
            partition = {}
            for name in names:
                signature = tuple(row['ports'][name]['kind'] for row in prefix)
                partition.setdefault(signature, []).append(name)
            groups = sorted(tuple(members) for members in partition.values())
            actions = sorted({tuple(row['action_nmu']) for row in prefix})
            cells, winners = [], []
            for members in groups:
                counts = []
                for action in actions:
                    support = set()
                    controls = 0
                    separating_actions = set()
                    for row in events[epoch:stop+1]:
                        raw_action = tuple(row['action_nmu'])
                        all_changed = all(row['ports'][name]['changed'] for name in members)
                        all_stable = all(not row['ports'][name]['changed'] for name in members)
                        if all_changed and raw_action == action:
                            support.add(tuple(tuple(row['ports'][name]['before_nmu']) for name in members))
                        if all_stable:
                            if raw_action == action:
                                controls += 1
                            if any(row['ports'][name]['changed'] for name in names if name not in members):
                                separating_actions.add(raw_action)
                    comparator = any(other != action for other in separating_actions)
                    omega = len(support)
                    counts.append({'action_nmu': list(action), 'omega': omega,
                                   'controls': controls, 'comparator': comparator})
                    if omega >= OMEGA_CRIT and controls and comparator:
                        winners.append((action, members))
                cells.append({'members': list(members), 'C_L_by_action': counts, 'xi': 0})
            if prior is not None and prior not in groups:
                final = {'status': 'REVOKED', 'action_nmu': None, 'members': None}
                prior = None
                epoch = stop+1
            elif len(winners) == 1:
                action, members = winners[0]
                final = {'status': 'CRYSTAL', 'action_nmu': list(action), 'members': list(members)}
                prior = members
                for cell in cells:
                    cell['xi'] = int(tuple(cell['members']) == members)
            elif prior is not None and not any(members == prior for _, members in winners):
                final = {'status': 'REVOKED', 'action_nmu': None, 'members': None}
            else:
                final = {'status': 'NO_PATH', 'action_nmu': None, 'members': None}
            expected = {'event_index': stop, 'source': event['source'],
                        'epoch_start': epoch, 'classes': cells, 'result': final}
            if canonical(expected) != canonical(certificate['phases'][stop]):
                return False
        return canonical(final) == canonical(certificate['result'])
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        return False

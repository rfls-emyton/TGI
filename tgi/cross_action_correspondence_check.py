"""Independent one-pass replay of every original cross-action event and phase."""
from tgi.frame_engine import canonical
from tgi.identity import REGISTRY_ID, decode
from tgi.organization import OMEGA_CRIT
from tgi.intervention_edit_contrast_check import verify as verify_contrast

REVISION = 'TGI-M1-CROSS-ACTION-PROFILE-RESEARCH-V3'


def verify(events, certificate):
    try:
        if (type(events) is not list or type(certificate) is not dict or
                set(certificate) != {'revision', 'registry', 'events', 'phases', 'result'} or
                certificate['revision'] != REVISION or certificate['registry'] != REGISTRY_ID or
                canonical(certificate['events']) != canonical(events) or
                type(certificate['phases']) is not list or len(certificate['phases']) != len(events)):
            return False
        if not events:
            return canonical(certificate['result']) == canonical({'status': 'NO_PATH', 'view': None})
        names = None
        sources = set()
        actions = set()
        comparator = set()
        support = {}
        controls = {}
        contradictions = {}
        prior_crystal = None
        final_result = {'status': 'NO_PATH', 'view': None}
        for index, event in enumerate(events):
            if (type(event) is not dict or set(event) != {'source', 'action_nmu', 'target', 'views'} or
                    type(event['source']) is not str or not event['source'] or event['source'] in sources or
                    type(event['action_nmu']) is not list or not event['action_nmu'] or
                    type(event['views']) is not dict or not verify_contrast(event['target'])):
                return False
            sources.add(event['source'])
            decode(event['action_nmu'])
            current_names = list(event['views'])
            if (len(current_names) < 2 or current_names != sorted(current_names) or
                    any(type(name) is not str or not name for name in current_names)):
                return False
            if names is None:
                names = current_names
                support = {name: {} for name in names}
                controls = {name: {} for name in names}
                contradictions = {name: [] for name in names}
            elif current_names != names:
                return False
            action = tuple(event['action_nmu'])
            actions.add(action)
            target_changed = event['target']['kind'] != 'STABLE'
            if not target_changed and any(view['kind'] != 'STABLE' for view in event['views'].values()):
                comparator.add(action)
            cells = []
            eligible = []
            for name in names:
                view = event['views'][name]
                if not verify_contrast(view):
                    return False
                view_changed = view['kind'] != 'STABLE'
                if target_changed and view_changed:
                    support[name].setdefault(action, set()).add(tuple(event['target']['before_nmu']))
                elif not target_changed and not view_changed:
                    controls[name][action] = controls[name].get(action, 0) + 1
                if event['target']['changed'] != view['changed']:
                    contradictions[name].append(event['source'])
                counts = [{'action_nmu': list(candidate),
                           'omega': len(support[name].get(candidate, ())),
                           'controls': controls[name].get(candidate, 0)}
                          for candidate in sorted(actions)]
                positives = [tuple(row['action_nmu']) for row in counts
                             if row['omega'] >= OMEGA_CRIT and row['controls']]
                if not contradictions[name] and any(a != b for a in positives for b in comparator):
                    eligible.append(name)
                cells.append({'view': name, 'omega_by_action': counts, 'xi': 0,
                              'contradicting_sources': list(contradictions[name])})
            if len(eligible) == 1:
                final_result = {'status': 'CRYSTAL', 'view': eligible[0]}
                prior_crystal = eligible[0]
                for cell in cells:
                    cell['xi'] = int(cell['view'] == prior_crystal)
            elif prior_crystal is not None and prior_crystal not in eligible:
                final_result = {'status': 'REVOKED', 'view': None}
            else:
                final_result = {'status': 'NO_PATH', 'view': None}
            expected = {'event_index': index, 'source': event['source'],
                        'comparator_actions': [list(a) for a in sorted(comparator)],
                        'cells': cells, 'result': final_result}
            if canonical(certificate['phases'][index]) != canonical(expected):
                return False
        return canonical(certificate['result']) == canonical(final_result)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        return False

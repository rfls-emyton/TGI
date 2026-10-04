"""Independent complete replay for V2 raw intervention certificates."""
from tgi.frame_engine import canonical
from tgi.identity import REGISTRY_ID, decode
from tgi.organization import OMEGA_CRIT
from tgi.intervention_edit_contrast_check import verify as verify_contrast

REVISION = 'TGI-M1-INTERVENTION-CORRESPONDENCE-RESEARCH-V2'


def verify(events, certificate):
    try:
        if (type(events) is not list or type(certificate) is not dict or
                set(certificate) != {'revision', 'registry', 'events', 'phases', 'result'} or
                certificate['revision'] != REVISION or certificate['registry'] != REGISTRY_ID or
                canonical(certificate['events']) != canonical(events) or
                type(certificate['phases']) is not list or len(certificate['phases']) != len(events)):
            return False
        sources = set()
        names = None
        action = None
        accepted = None
        expected_phases = []
        for index, event in enumerate(events):
            if (type(event) is not dict or
                    set(event) != {'source', 'action_nmu', 'target', 'views'} or
                    type(event['source']) is not str or not event['source'] or
                    event['source'] in sources or
                    type(event['action_nmu']) is not list or not event['action_nmu'] or
                    type(event['views']) is not dict):
                return False
            sources.add(event['source'])
            decode(event['action_nmu'])
            if not verify_contrast(event['target']):
                return False
            current_names = list(event['views'])
            if (len(current_names) < 2 or current_names != sorted(current_names) or
                    any(type(name) is not str or not name for name in current_names)):
                return False
            if names is None:
                names = current_names
                action = event['action_nmu']
            if current_names != names:
                return False
            if event['action_nmu'] != action:
                return False
            for name in names:
                view = event['views'][name]
                if not verify_contrast(view):
                    return False
            prefix = events[:index + 1]
            controls = sum(not row['target']['changed'] for row in prefix)
            cells = []
            eligible = []
            for name in names:
                supporting = {tuple(row['target']['before_nmu']) for row in prefix
                              if row['target']['changed'] and row['views'][name]['changed']}
                opposing = [row['source'] for row in prefix
                            if row['target']['changed'] != row['views'][name]['changed']]
                if not opposing and controls and len(supporting) >= OMEGA_CRIT:
                    eligible.append(name)
                cells.append({'view': name, 'omega': len(supporting),
                              'xi': 0, 'contradicting_sources': opposing})
            if len(eligible) == 1:
                result = {'status': 'CRYSTAL', 'view': eligible[0]}
                accepted = eligible[0]
                for cell in cells:
                    cell['xi'] = int(cell['view'] == accepted)
            elif accepted is not None and accepted not in eligible:
                result = {'status': 'REVOKED', 'view': None}
            else:
                result = {'status': 'NO_PATH', 'view': None}
            expected_phases.append({'event_index': index, 'source': event['source'],
                                    'controls': controls, 'cells': cells,
                                    'result': result})
        expected_result = (expected_phases[-1]['result'] if expected_phases else
                           {'status': 'NO_PATH', 'view': None})
        return (canonical(certificate['phases']) == canonical(expected_phases) and
                canonical(certificate['result']) == canonical(expected_result))
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        return False

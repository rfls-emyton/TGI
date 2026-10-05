"""Independent raw replay of action-conditioned local response cells."""

from .frame_engine import canonical
from .identity import REGISTRY_ID, encode
from .organization import OMEGA_CRIT

REVISION = 'TGI-M2-PHASE-BOUND-RESPONSE-ATLAS-V1'


def verify(events, certificate):
    try:
        if type(events) is not list or type(certificate) is not dict or \
                set(certificate) != {'revision', 'registry', 'phases', 'decision'} or \
                certificate['revision'] != REVISION or \
                certificate['registry'] != REGISTRY_ID:
            return False
        previous_keys, previous_births, previous_roles = set(), {}, set()
        expected_phases = []
        names = None
        prepared = []
        for index in range(len(events)):
            row = events[index]
            if type(row) is not dict or set(row) != {'source', 'action', 'ports'}:
                return False
            current_names = sorted(row['ports'])
            if names is None:
                names = current_names
            if current_names != names or len(names) < 3:
                return False
            prepared.append({'action': tuple(encode(row['action'])),
                             'before': {port: tuple(encode(row['ports'][port][0]))
                                        for port in names},
                             'changed': {port: row['ports'][port][0] != row['ports'][port][1]
                                         for port in names}})
            actions = sorted({item['action'] for item in prepared})
            current_keys, new_births, admitted, cells = set(), {}, set(), []
            for action in actions:
                action_rows = [item for item in prepared if item['action'] == action]
                patterns = {}
                for port in names:
                    pattern = tuple(item['changed'][port] for item in action_rows)
                    patterns.setdefault(pattern, []).append(port)
                for members in sorted(tuple(ports) for ports in patterns.values()):
                    key = (action, members)
                    current_keys.add(key)
                    born = previous_births[key] if key in previous_keys else index
                    new_births[key] = born
                    c_contexts, all_c, l_contexts = set(), set(), set()
                    l_events = 0
                    other_action = False
                    for position, item in enumerate(prepared):
                        candidate_action = item['action']
                        context = tuple(item['before'][port] for port in members)
                        c = all(item['changed'][port] for port in members)
                        l = all(not item['changed'][port] for port in members)
                        if candidate_action == action:
                            if c:
                                all_c.add(context)
                                if position >= born:
                                    c_contexts.add(context)
                            if l:
                                l_contexts.add(context)
                                l_events += 1
                        elif l and any(item['changed'][port]
                                       for port in names if port not in members):
                            other_action = True
                    opposed = bool(all_c & l_contexts)
                    crystallized = (len(c_contexts) >= OMEGA_CRIT and l_events > 0
                                   and other_action and not opposed)
                    cells.append({'action_nmu': list(action), 'members': list(members),
                                  'born_at': born, 'omega': len(c_contexts),
                                  'controls': l_events, 'comparator': other_action,
                                  'opposition': opposed, 'xi': int(crystallized)})
                    if crystallized:
                        admitted.add(key)
            granted = [{'action_nmu': list(action), 'members': list(members)}
                       for action, members in sorted(admitted)]
            revoked = [{'action_nmu': list(action), 'members': list(members)}
                       for action, members in sorted(previous_roles-admitted)]
            expected_phases.append({
                'event_index': index, 'source': row['source'], 'classes': cells,
                'admitted': granted, 'revoked': revoked,
                'status': 'CRYSTAL' if granted else 'REVOKED' if revoked else 'NO_PATH'})
            previous_keys, previous_births, previous_roles = current_keys, new_births, admitted
        decision = expected_phases[-1] if expected_phases else {
            'event_index': None, 'source': None, 'classes': [], 'admitted': [],
            'revoked': [], 'status': 'NO_PATH'}
        expected = {'revision': REVISION, 'registry': REGISTRY_ID,
                    'phases': expected_phases, 'decision': decision}
        return canonical(expected) == canonical(certificate)
    except (KeyError, ValueError, TypeError, IndexError, AttributeError):
        return False

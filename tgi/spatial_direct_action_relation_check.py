"""Independent certificate reconstruction for phase-owned direct action relations."""
from hashlib import sha256

from .frame_engine import canonical
from .identity import encode, REGISTRY_ID
from .organization import RawOrganization, OMEGA_CRIT


def verify_direct_raw_relation(model, commands, certificate):
    try:
        if (type(model) is not RawOrganization or model.frames._pending or
                type(commands) is not list or type(certificate) is not dict or
                len(commands) != len(model.episodes)):
            return False
        if (set(certificate) != {'policy', 'registry', 'threshold', 'source_count', 'relations'} or
                certificate['policy'] != 'm1_spatial_action_relation_v1' or
                certificate['registry'] != REGISTRY_ID or
                certificate['threshold'] != OMEGA_CRIT or
                type(certificate['relations']) is not list):
            return False
        seen = set()
        grouped = {}
        for command in commands:
            if type(command) is not dict or set(command) != {'source', 'action'}:
                return False
            source, action = command['source'], command['action']
            if (type(source) is not str or type(action) is not str or not action or
                    source in seen or source not in model.episodes or not model._alive(source)):
                return False
            seen.add(source)
            frames, receipts = model.episodes[source]
            if len(frames) != 2 or len(frames[0]) != len(frames[1]):
                return False
            changes = [index for index in range(len(frames[0])) if frames[0][index] != frames[1][index]]
            dot = encode('.')[0]
            if (len(changes) != 1 or frames[0][changes[0]] == dot or
                    frames[1][changes[0]] == dot):
                return False
            port = changes[0]
            action_ids = tuple(encode(action))
            old, new = frames[0][port], frames[1][port]
            event = {'source': source, 'action_nmu': list(action_ids),
                     'before_nmu': list(frames[0]), 'after_nmu': list(frames[1]),
                     'port': port, 'input_nmu': old, 'output_nmu': new,
                     'context': [list(frames[0]), port],
                     'before_origin': list(receipts[0].origin),
                     'after_origin': list(receipts[1].origin)}
            grouped.setdefault((action_ids, old), []).append(event)
        if certificate['source_count'] != len(seen) or seen != set(model.episodes):
            return False
        expected = []
        for (action_ids, old), events in sorted(grouped.items()):
            events.sort(key=lambda row: row['source'])
            outputs = sorted({row['output_nmu'] for row in events})
            contexts = {canonical(row['context']) for row in events}
            omega = min(len(events), len(contexts))
            phase = 'REVOKED' if len(outputs) > 1 else 'CRYSTAL' if omega >= OMEGA_CRIT else 'LIQUID'
            expected.append({'anchor': sha256(canonical([list(action_ids), old]).encode()).hexdigest(),
                             'action_nmu': list(action_ids), 'input_nmu': old,
                             'output_nmu': outputs[0] if len(outputs) == 1 else None,
                             'candidate_outputs': outputs, 'omega_relation': omega,
                             'xi_relation': int(phase == 'CRYSTAL'), 'status': phase,
                             'support_sources': [row['source'] for row in events],
                             'context_count': len(contexts), 'witnesses': events})
        return canonical(certificate['relations']) == canonical(expected)
    except (AttributeError, IndexError, KeyError, TypeError, ValueError):
        return False

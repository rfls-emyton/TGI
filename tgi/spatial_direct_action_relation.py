"""Research derivation of action relations from phase-valid raw pairs alone."""
from hashlib import sha256

from .frame_engine import canonical
from .identity import encode, decode, REGISTRY_ID
from .organization import RawOrganization, OMEGA_CRIT

POLICY = 'm1_spatial_action_relation_v1'


def form_direct_raw_relations(model, commands):
    if type(model) is not RawOrganization or model.frames._pending or type(commands) is not list:
        raise ValueError('Complete source-owned raw crystal episodes required')
    if len(commands) != len(model.episodes):
        raise ValueError('Every raw episode needs one observed action')
    events, seen = [], set()
    for command in commands:
        if type(command) is not dict or set(command) != {'source', 'action'}:
            raise ValueError('Portless source-owned command required')
        source, action = command['source'], command['action']
        if (type(source) is not str or type(action) is not str or not action or
                source in seen or source not in model.episodes or not model._alive(source)):
            raise ValueError('Unique live crystal pair and raw action required')
        seen.add(source)
        frames, receipts = model.episodes[source]
        if len(frames) != 2:
            raise ValueError('Before/after crystal pair required')
        before, after = map(decode, frames)
        if len(before) != len(after):
            raise ValueError('Equal-length raw frames required')
        changed = [index for index, (left, right) in enumerate(zip(before, after)) if left != right]
        if len(changed) != 1 or before[changed[0]] == '.' or after[changed[0]] == '.':
            raise ValueError('One persistent changed occurrence required')
        port = changed[0]
        events.append({'source': source, 'action_nmu': list(encode(action)),
                       'before_nmu': list(frames[0]), 'after_nmu': list(frames[1]),
                       'port': port, 'input_nmu': frames[0][port], 'output_nmu': frames[1][port],
                       'context': [list(frames[0]), port],
                       'before_origin': list(receipts[0].origin),
                       'after_origin': list(receipts[1].origin)})
    groups = {}
    for event in events:
        key = (tuple(event['action_nmu']), event['input_nmu'])
        groups.setdefault(key, []).append(event)
    relations = []
    for (action_nmu, input_nmu), witnesses in sorted(groups.items()):
        witnesses = sorted(witnesses, key=lambda event: event['source'])
        contexts = {canonical(event['context']) for event in witnesses}
        outputs = sorted({event['output_nmu'] for event in witnesses})
        omega = min(len(witnesses), len(contexts))
        status = 'REVOKED' if len(outputs) > 1 else 'CRYSTAL' if omega >= OMEGA_CRIT else 'LIQUID'
        relations.append({'anchor': sha256(canonical([list(action_nmu), input_nmu]).encode()).hexdigest(),
                          'action_nmu': list(action_nmu), 'input_nmu': input_nmu,
                          'output_nmu': outputs[0] if len(outputs) == 1 else None,
                          'candidate_outputs': outputs, 'omega_relation': omega,
                          'xi_relation': 1 if status == 'CRYSTAL' else 0,
                          'status': status, 'support_sources': [event['source'] for event in witnesses],
                          'context_count': len(contexts), 'witnesses': witnesses})
    return {'policy': POLICY, 'registry': REGISTRY_ID, 'threshold': OMEGA_CRIT,
            'source_count': len(events), 'relations': relations}

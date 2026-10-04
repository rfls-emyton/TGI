"""Local relation transition over a previously verified crystal certificate.

The caller owns the old certificate and supplies one newly phase-verified raw
event.  Full raw replay remains the admission check at checkpoint/recovery.
"""
from hashlib import sha256

from .frame_engine import canonical
from .identity import encode
from .organization import OMEGA_CRIT, RawOrganization


def event_from_new_raw_pair(model, source, action):
    """Prove only the newly published source, then derive its observed port."""
    if (type(model) is not RawOrganization or model.frames._pending or
            type(source) is not str or type(action) is not str or not action or
            source not in model.episodes or not model._alive(source)):
        raise ValueError('New live raw crystal pair required')
    frames, receipts = model.episodes[source]
    if len(frames) != 2 or len(frames[0]) != len(frames[1]):
        raise ValueError('Equal-length before/after pair required')
    changed = [index for index, (left, right) in enumerate(zip(*frames)) if left != right]
    dot = encode('.')[0]
    if len(changed) != 1 or frames[0][changed[0]] == dot or frames[1][changed[0]] == dot:
        raise ValueError('One persistent changed occurrence required')
    port = changed[0]
    return {'source': source, 'action_nmu': list(encode(action)),
            'before_nmu': list(frames[0]), 'after_nmu': list(frames[1]),
            'port': port, 'input_nmu': frames[0][port], 'output_nmu': frames[1][port],
            'context': [list(frames[0]), port],
            'before_origin': list(receipts[0].origin),
            'after_origin': list(receipts[1].origin)}


def append_verified_event(certificate, event):
    if certificate['threshold'] != OMEGA_CRIT or certificate['source_count'] < 0:
        raise ValueError('Unexpected relation certificate')
    if event['source'] in (source for relation in certificate['relations']
                           for source in relation['support_sources']):
        raise ValueError('Duplicate source')
    key = (tuple(event['action_nmu']), event['input_nmu'])
    relations = list(certificate['relations'])
    index = next((i for i, relation in enumerate(relations)
                  if (tuple(relation['action_nmu']), relation['input_nmu']) == key), None)
    witnesses = [] if index is None else list(relations[index]['witnesses'])
    witnesses.append(event)
    witnesses.sort(key=lambda row: row['source'])
    outputs = sorted({row['output_nmu'] for row in witnesses})
    contexts = {canonical(row['context']) for row in witnesses}
    omega = min(len(witnesses), len(contexts))
    status = 'REVOKED' if len(outputs) > 1 else 'CRYSTAL' if omega >= OMEGA_CRIT else 'LIQUID'
    relation = {'anchor': sha256(canonical([list(key[0]), key[1]]).encode()).hexdigest(),
                'action_nmu': list(key[0]), 'input_nmu': key[1],
                'output_nmu': outputs[0] if len(outputs) == 1 else None,
                'candidate_outputs': outputs, 'omega_relation': omega,
                'xi_relation': int(status == 'CRYSTAL'), 'status': status,
                'support_sources': [row['source'] for row in witnesses],
                'context_count': len(contexts), 'witnesses': witnesses}
    if index is None:
        relations.append(relation)
    else:
        relations[index] = relation
    relations.sort(key=lambda row: (tuple(row['action_nmu']), row['input_nmu']))
    return {**certificate, 'source_count': certificate['source_count'] + 1,
            'relations': relations}


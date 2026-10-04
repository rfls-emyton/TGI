"""Choose untried raw NMU actions for a crystallized ambiguous port class."""
from copy import deepcopy
from hashlib import sha256

from tgi.frame_engine import canonical
from tgi.identity import encode
from tgi.local_edit_transport_classes_check import verify as verify_classes


def certify_port_distinction(certificate, available_actions):
    if not isinstance(certificate, dict) or not verify_classes(
            certificate.get('events'), certificate):
        raise ValueError('Verified original V4 class certificate required')
    if not isinstance(available_actions, (list, tuple)) or not available_actions:
        raise ValueError('Finite nonempty raw action catalogue required')
    if any(type(action) is not str or not action for action in available_actions):
        raise ValueError('Nonempty raw action strings required')
    if len(set(available_actions)) != len(available_actions):
        raise ValueError('Duplicate raw action')
    actions = sorted(available_actions, key=lambda action: tuple(encode(action)))
    phase = certificate['phases'][-1] if certificate['phases'] else None
    result = certificate['result']
    active = result['status'] == 'CRYSTAL' and len(result['members']) > 1
    start = phase['epoch_start'] if active else None
    observed = {tuple(event['action_nmu']) for event in certificate['events'][start:]} if active else set()
    coverage = [{'action': action, 'action_nmu': list(encode(action)),
                 'observed_in_epoch': tuple(encode(action)) in observed}
                for action in actions]
    alternatives = [row['action'] for row in coverage if active and not row['observed_in_epoch']]
    selection = alternatives[0] if alternatives else None
    return {'policy': 'port_distinction_exploration_v1',
            'class_sha256': sha256(canonical(certificate).encode('utf8')).hexdigest(),
            'epoch_start': start, 'members': deepcopy(result['members']) if active else None,
            'coverage': coverage, 'alternatives': alternatives,
            'result': {'status': 'SELECT' if selection else 'NO_UNTRIED_ACTION' if active else 'NO_AMBIGUOUS_CRYSTAL',
                       'selected_action': selection, 'effect_predicted': False,
                       'separation_claimed': False}}

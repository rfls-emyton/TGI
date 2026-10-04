"""Independent replay of finite-catalogue distinction selection."""
from hashlib import sha256

from tgi.frame_engine import canonical
from tgi.identity import encode
from tgi.local_edit_transport_classes_check import verify as verify_classes


def verify_port_distinction(certificate, available_actions, candidate):
    try:
        if not isinstance(certificate, dict) or not verify_classes(
                certificate.get('events'), certificate):
            return False
        if not isinstance(available_actions, (list, tuple)) or not available_actions:
            return False
        if any(type(action) is not str or not action for action in available_actions):
            return False
        if len(set(available_actions)) != len(available_actions):
            return False
        ordered = sorted((tuple(encode(action)), action) for action in available_actions)
        last = certificate['phases'][-1] if certificate['phases'] else None
        outcome = certificate['result']
        active = outcome['status'] == 'CRYSTAL' and len(outcome['members']) > 1
        start = last['epoch_start'] if active else None
        seen = {tuple(row['action_nmu']) for row in certificate['events'][start:]} if active else set()
        rows = [{'action': action, 'action_nmu': list(ids),
                 'observed_in_epoch': ids in seen} for ids, action in ordered]
        alternatives = [row['action'] for row in rows if active and not row['observed_in_epoch']]
        first = alternatives[0] if alternatives else None
        expected = {'policy': 'port_distinction_exploration_v1',
                    'class_sha256': sha256(canonical(certificate).encode('utf8')).hexdigest(),
                    'epoch_start': start,
                    'members': list(outcome['members']) if active else None,
                    'coverage': rows, 'alternatives': alternatives,
                    'result': {'status': 'SELECT' if first else 'NO_UNTRIED_ACTION' if active else 'NO_AMBIGUOUS_CRYSTAL',
                               'selected_action': first, 'effect_predicted': False,
                               'separation_claimed': False}}
        return type(candidate) is dict and candidate == expected
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        return False

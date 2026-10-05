"""Raw NMU endpoint transport from phase-bound action roles and source crystals."""

import hashlib
import json
import os
import re
import tempfile
from copy import deepcopy
from pathlib import Path

from .frame_engine import canonical, unique_object
from .identity import REGISTRY_ID, decode, encode
from .lineage_state import certify_lineage_state
from .organization_snapshot import snapshot
from .phase_bound_response_atlas import PhaseBoundResponseAtlas

POLICY = 'source_bound_endpoint_transport_v1'


def _sha(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def _project(epoch):
    model, groups, measurements = epoch
    view = snapshot(model)
    events, observations, seen = [], {}, set()
    for index, group in enumerate(groups):
        if type(group) is not list or len(group) < 3:
            raise ValueError('Three original port streams per event required')
        ports, actions, sources = {}, set(), {}
        for spec in group:
            if type(spec) is not dict or set(spec) != {'port', 'source'}:
                raise ValueError('Original source and port mapping required')
            port, source = spec['port'], spec['source']
            if port in ports or source in seen or source not in view.episodes or \
                    not view._alive(source):
                raise ValueError('Unique live original source required')
            seen.add(source)
            frames = view.episodes[source][0]
            if len(frames) != 3:
                raise ValueError('Before, action, after crystal required')
            before, action, after = map(decode, frames)
            actions.add(action)
            ports[port] = [before, after]
            sources[port] = source
            observations.setdefault(port, []).append(
                {'source': source, 'before': before, 'action': action, 'after': after})
        if len(actions) != 1:
            raise ValueError('Group action differs across original port sources')
        events.append({'source': f'event-{index}', 'action': actions.pop(),
                       'ports': ports})
    if seen != set(view.episodes):
        raise ValueError('Acquisition has unowned crystal sources')
    atlas = PhaseBoundResponseAtlas(events)
    return atlas, events, observations


def _step(rows, before, action):
    direct = [row for row in rows if row['before'] == before and row['action'] == action]
    if direct:
        outcomes = {row['after'] for row in direct}
        if len(outcomes) != 1:
            return {'status': 'OBSERVED_CONFLICT', 'output': [],
                    'mode': None, 'suffix_nmu': [],
                    'source_ids': sorted(row['source'] for row in direct)}
        output = next(iter(outcomes))
        if output == before:
            before_ids = encode(before)
            for length in range(len(before_ids), 0, -1):
                suffix = before_ids[-length:]
                others = [row for row in rows if row['action'] == action and
                          row['before'] != before and
                          encode(row['before'])[-length:] == suffix]
                if len({row['before'] for row in others}) >= 2 and \
                        all(row['after'] == decode(encode(row['before'])+encode(action))
                            for row in others):
                    return {'status': 'OBSERVED_CONFLICT', 'output': [],
                            'mode': None, 'suffix_nmu': list(suffix),
                            'source_ids': sorted(row['source'] for row in others+direct)}
        if output not in (before, decode(encode(before)+encode(action))):
            return {'status': 'NO_PATH', 'output': [], 'mode': None,
                    'suffix_nmu': [], 'source_ids': sorted(row['source'] for row in direct)}
        return {'status': 'RESOLVED', 'output': [output],
                'mode': 'DIRECT_APPEND' if output != before else 'DIRECT_STABLE',
                'suffix_nmu': [],
                'source_ids': sorted(row['source'] for row in direct)}
    before_ids = encode(before)
    for length in range(len(before_ids), 0, -1):
        suffix = before_ids[-length:]
        matched = [row for row in rows if row['action'] == action and
                   encode(row['before'])[-length:] == suffix]
        if len({row['before'] for row in matched}) < 2:
            continue
        if any(row['after'] != decode(encode(row['before'])+encode(action))
               for row in matched):
            continue
        return {'status': 'RESOLVED',
                'output': [decode(before_ids+encode(action))],
                'mode': 'SUFFIX_ENDPOINT_TRANSPORT',
                'suffix_nmu': list(suffix),
                'source_ids': sorted(row['source'] for row in matched)}
    return {'status': 'NO_PATH', 'output': [], 'mode': None,
            'suffix_nmu': [], 'source_ids': []}


def certify_source_bound_endpoint_transport(old, bridge, new, root_port,
                                            anchor, actions):
    if type(actions) not in (list, tuple) or not actions or \
            any(type(action) is not str or not action for action in actions):
        raise ValueError('Ordered nonempty raw actions required')
    state = certify_lineage_state(old, bridge, new, root_port, anchor, actions)
    atlas, events, observations = _project(new)
    atlas_certificate, action_roles = atlas.resolve_batch_with_certificate(actions)
    port = state['port']
    seed = state['result']['seed'][0] if state['result']['status'] == 'OBSERVED_STATE_READY' else None
    result = {'policy': POLICY, 'registry': REGISTRY_ID,
              'state': state, 'port': port,
              'event_sha256': _sha(events),
              'atlas_certificate_sha256': _sha(atlas_certificate),
              'steps': [], 'result': None}
    if seed is None:
        result['result'] = {'status': state['result']['status'],
                            'output': [], 'lineage': [], 'completed_steps': 0}
        return result
    current = seed
    owners = [{'kind': 'seed', 'position': index}
              for index in range(len(encode(seed)))]
    for index, action in enumerate(actions):
        classes = action_roles[index]
        if not classes or not any(port in members for members in classes):
            step = {'before': current, 'action': action, 'status': 'NO_ROLE',
                    'mode': None, 'output': [], 'suffix_nmu': [],
                    'source_ids': [], 'lineage': []}
        else:
            decision = _step(observations[port], current, action)
            step = {'before': current, 'action': action, **decision,
                    'lineage': []}
            if decision['status'] == 'RESOLVED':
                output = decision['output'][0]
                lineage = [dict(owner) for owner in owners]
                if output != current:
                    lineage.extend({'kind': 'action', 'step': index,
                                    'position': position}
                                   for position in range(len(encode(action))))
                step['lineage'] = lineage
        result['steps'].append(step)
        if step['status'] != 'RESOLVED':
            result['result'] = {
                'status': ('OBSERVATION_CONTRADICTION' if step['status'] == 'OBSERVED_CONFLICT'
                           else 'NO_PATH'), 'output': [], 'lineage': [],
                'completed_steps': index}
            break
        current = step['output'][0]
        owners = step['lineage']
    else:
        result['result'] = {'status': 'GEOMETRIC_KNOWLEDGE_SUPPORTED',
                            'output': [current], 'lineage': deepcopy(owners),
                            'completed_steps': len(actions)}
    return result


def commit_source_bound_endpoint_transport(old, bridge, new, root_port,
                                           anchor, actions, certificate, path):
    from .source_bound_endpoint_transport_check import verify_source_bound_endpoint_transport
    if not verify_source_bound_endpoint_transport(old, bridge, new, root_port,
                                                  anchor, actions, certificate):
        raise ValueError('Only a verified current endpoint certificate may be committed')
    payload = {'policy': POLICY, 'registry': REGISTRY_ID,
               'root_port': root_port, 'anchor': deepcopy(anchor),
               'actions': list(actions), 'certificate': deepcopy(certificate)}
    envelope = {'payload': payload, 'sha256': _sha(payload)}
    data = canonical(envelope).encode('utf8')
    target = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='wb', dir=target.parent,
                                         delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return {'path': str(target), 'sha256': hashlib.sha256(data).hexdigest(),
            'bytes': len(data)}


def recover_source_bound_endpoint_transport(old, bridge, new, root_port,
                                            anchor, actions, path, expected_sha256):
    from .source_bound_endpoint_transport_check import verify_source_bound_endpoint_transport
    if type(expected_sha256) is not str or re.fullmatch('[0-9a-f]{64}', expected_sha256) is None:
        raise ValueError('External endpoint checkpoint digest required')
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError('Endpoint checkpoint digest mismatch')
    envelope = json.loads(data.decode('utf8'), object_pairs_hook=unique_object)
    if type(envelope) is not dict or set(envelope) != {'payload', 'sha256'}:
        raise ValueError('Invalid endpoint checkpoint envelope')
    payload = envelope['payload']
    if type(payload) is not dict or set(payload) != {
            'policy', 'registry', 'root_port', 'anchor', 'actions', 'certificate'} or \
            payload['policy'] != POLICY or payload['registry'] != REGISTRY_ID or \
            payload['root_port'] != root_port or \
            canonical(payload['anchor']) != canonical(anchor) or \
            canonical(payload['actions']) != canonical(list(actions)) or \
            envelope['sha256'] != _sha(payload):
        raise ValueError('Invalid endpoint checkpoint payload')
    certificate = payload['certificate']
    if not verify_source_bound_endpoint_transport(old, bridge, new, root_port,
                                                  anchor, actions, certificate):
        raise ValueError('Endpoint certificate disagrees with live source')
    return certificate

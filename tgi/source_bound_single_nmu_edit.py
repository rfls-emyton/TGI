"""Lineage-bound, source-owned one-NMU substitution transport."""
import hashlib
import json
import os
import re
import tempfile
from copy import deepcopy
from pathlib import Path

from .frame_engine import canonical, unique_object
from .identity import REGISTRY_ID, encode, decode
from .lineage_state import certify_lineage_state
from .source_bound_endpoint_transport import _project

POLICY = 'source_bound_single_nmu_edit_v1'


def _digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def _pair(before, after):
    left, right = encode(before), encode(after)
    if len(left) != len(right):
        return None
    positions = [i for i, (a, b) in enumerate(zip(left, right)) if a != b]
    return (left[positions[0]], right[positions[0]]) if len(positions) == 1 else None


def _lineage(seed, output, sources):
    left, right = encode(seed), encode(output)
    changed = [i for i, (a, b) in enumerate(zip(left, right)) if a != b]
    return [({'kind': 'witness', 'position': i, 'source_ids': sources}
             if i in changed else {'kind': 'seed', 'position': i})
            for i in range(len(right))]


def _decide(rows, seed, action):
    direct = [r for r in rows if r['before'] == seed and r['action'] == action]
    if direct:
        sources = sorted(r['source'] for r in direct)
        values = {r['after'] for r in direct}
        if len(values) != 1:
            return 'OBSERVATION_CONTRADICTION', None, None, sources, None
        output = next(iter(values))
        if output != seed and _pair(seed, output) is None:
            return 'NO_PATH', None, None, sources, None
        return 'RESOLVED', 'DIRECT', output, sources, _pair(seed, output)
    candidates = {}
    for row in rows:
        if row['action'] != action:
            continue
        pair = _pair(row['before'], row['after'])
        if pair is not None and encode(row['before']).count(pair[0]) == 1:
            candidates.setdefault(pair, []).append(row)
    accepted = []
    for pair, support in candidates.items():
        removed, added = pair
        relevant = [r for r in rows if r['action'] == action and
                    encode(r['before']).count(removed) == 1]
        if len({r['before'] for r in support}) < 2 or \
           len(support) != len(relevant) or encode(seed).count(removed) != 1:
            continue
        ids = list(encode(seed))
        ids[ids.index(removed)] = added
        accepted.append((pair, decode(ids), sorted(r['source'] for r in support)))
    if len(accepted) != 1:
        return 'NO_PATH', None, None, [], None
    pair, output, sources = accepted[0]
    return 'RESOLVED', 'HELDOUT_SUBSTITUTE', output, sources, pair


def certify_source_bound_single_nmu_edit(old, bridge, new, root_port,
                                         anchor, action):
    if type(action) is not str or not action:
        raise ValueError('One nonempty raw action required')
    state = certify_lineage_state(old, bridge, new, root_port, anchor, [action])
    atlas, events, observations = _project(new)
    port = state['port']
    atlas_certificate, action_roles = atlas.resolve_batch_with_certificate([action])
    certificate = {'policy': POLICY, 'registry': REGISTRY_ID, 'state': state,
                   'port': port, 'event_sha256': _digest(events),
                   'atlas_certificate_sha256': _digest(atlas_certificate),
                   'result': None}
    if state['result']['status'] != 'OBSERVED_STATE_READY':
        certificate['result'] = {'status': state['result']['status'], 'mode': None,
                                 'output': [], 'pair_nmu': [], 'source_ids': [],
                                 'lineage': []}
        return certificate
    direct = [row for row in observations[port] if
              row['before'] == state['result']['seed'][0] and row['action'] == action]
    if len({row['after'] for row in direct}) > 1:
        status, mode, output, sources, pair = (
            'OBSERVATION_CONTRADICTION', None, None,
            sorted(row['source'] for row in direct), None)
    elif not (action_roles[0] and
              any(port in members for members in action_roles[0])):
        status, mode, output, sources, pair = 'NO_PATH', None, None, [], None
    else:
        status, mode, output, sources, pair = _decide(
            observations[port], state['result']['seed'][0], action)
    certificate['result'] = {'status': status, 'mode': mode,
                             'output': [output] if output is not None else [],
                             'pair_nmu': list(pair) if pair else [],
                             'source_ids': sources,
                             'lineage': _lineage(state['result']['seed'][0], output,
                                                 sources) if output is not None else []}
    return certificate


def commit_source_bound_single_nmu_edit(old, bridge, new, root_port,
                                        anchor, action, certificate, path):
    from .source_bound_single_nmu_edit_check import verify_source_bound_single_nmu_edit
    if not verify_source_bound_single_nmu_edit(old, bridge, new, root_port,
                                               anchor, action, certificate):
        raise ValueError('Only a verified current edit certificate may be committed')
    payload = {'policy': POLICY, 'registry': REGISTRY_ID, 'root_port': root_port,
               'anchor': deepcopy(anchor), 'action': action,
               'certificate': deepcopy(certificate)}
    data = canonical({'payload': payload, 'sha256': _digest(payload)}).encode('utf8')
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


def recover_source_bound_single_nmu_edit(old, bridge, new, root_port,
                                         anchor, action, path, expected_sha256):
    from .source_bound_single_nmu_edit_check import verify_source_bound_single_nmu_edit
    if type(expected_sha256) is not str or re.fullmatch('[0-9a-f]{64}', expected_sha256) is None:
        raise ValueError('External edit checkpoint digest required')
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError('Edit checkpoint digest mismatch')
    envelope = json.loads(data.decode('utf8'), object_pairs_hook=unique_object)
    if type(envelope) is not dict or set(envelope) != {'payload', 'sha256'}:
        raise ValueError('Invalid edit checkpoint envelope')
    payload = envelope['payload']
    if type(payload) is not dict or set(payload) != {
            'policy', 'registry', 'root_port', 'anchor', 'action', 'certificate'} or \
            payload['policy'] != POLICY or payload['registry'] != REGISTRY_ID or \
            payload['root_port'] != root_port or \
            canonical(payload['anchor']) != canonical(anchor) or \
            payload['action'] != action or envelope['sha256'] != _digest(payload):
        raise ValueError('Invalid edit checkpoint payload')
    certificate = payload['certificate']
    if not verify_source_bound_single_nmu_edit(old, bridge, new, root_port,
                                                anchor, action, certificate):
        raise ValueError('Edit certificate disagrees with live source')
    return certificate

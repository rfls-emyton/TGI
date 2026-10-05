"""Independent source, role, suffix, output and NMU-lineage replay."""

import hashlib

from .frame_engine import canonical
from .identity import REGISTRY_ID, decode, encode
from .lineage_state_check import verify_lineage_state
from .organization_snapshot import snapshot
from .phase_bound_response_atlas import PhaseBoundResponseAtlas

POLICY = 'source_bound_endpoint_transport_v1'


def _digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def verify_source_bound_endpoint_transport(old, bridge, new, root_port,
                                           anchor, actions, certificate):
    try:
        c = certificate
        if type(c) is not dict or set(c) != {
                'policy', 'registry', 'state', 'port', 'event_sha256',
                'atlas_certificate_sha256', 'steps', 'result'} or \
                c['policy'] != POLICY or c['registry'] != REGISTRY_ID or \
                type(actions) not in (list, tuple) or not actions or \
                any(type(action) is not str or not action for action in actions):
            return False
        if not verify_lineage_state(old, bridge, new, root_port, anchor,
                                    actions, c['state']):
            return False
        model, groups, _ = new
        view = snapshot(model)
        seen, events, observations = set(), [], {}
        for index, group in enumerate(groups):
            if type(group) is not list or len(group) < 3:
                return False
            actions_in_group, ports = set(), {}
            for spec in group:
                if type(spec) is not dict or set(spec) != {'port', 'source'}:
                    return False
                source, port = spec['source'], spec['port']
                if source in seen or source not in view.episodes or \
                        port in ports or not view._alive(source):
                    return False
                seen.add(source)
                frames = view.episodes[source][0]
                if len(frames) != 3:
                    return False
                before, action, after = [decode(frame) for frame in frames]
                actions_in_group.add(action)
                ports[port] = [before, after]
                observations.setdefault(port, []).append((source, before,
                                                            action, after))
            if len(actions_in_group) != 1:
                return False
            events.append({'source': f'event-{index}',
                           'action': actions_in_group.pop(), 'ports': ports})
        if seen != set(view.episodes) or _digest(events) != c['event_sha256']:
            return False
        atlas = PhaseBoundResponseAtlas(events)
        if _digest(atlas.certificate) != c['atlas_certificate_sha256']:
            return False
        port = c['state']['port']
        if c['port'] != port:
            return False
        ready = c['state']['result']['status'] == 'OBSERVED_STATE_READY'
        if not ready:
            expected = {'status': c['state']['result']['status'], 'output': [],
                        'lineage': [], 'completed_steps': 0}
            return c['steps'] == [] and canonical(c['result']) == canonical(expected)
        current = c['state']['result']['seed'][0]
        owners = [{'kind': 'seed', 'position': position}
                  for position in range(len(encode(current)))]
        expected_steps = []
        for index, action in enumerate(actions):
            roles = atlas.resolve(action)
            status, mode, output, suffix, sources = 'NO_ROLE', None, [], [], []
            if roles and any(port in members for members in roles):
                rows = observations[port]
                direct = [row for row in rows if row[1] == current and row[2] == action]
                if direct:
                    values = {row[3] for row in direct}
                    sources = sorted(row[0] for row in direct)
                    if len(values) != 1:
                        status = 'OBSERVED_CONFLICT'
                    else:
                        observed = next(iter(values))
                        expected_append = decode(encode(current)+encode(action))
                        if observed == current:
                            ids = encode(current)
                            for length in range(len(ids), 0, -1):
                                candidate = ids[-length:]
                                others = [row for row in rows if row[2] == action and
                                          row[1] != current and
                                          encode(row[1])[-length:] == candidate]
                                if len({row[1] for row in others}) >= 2 and all(
                                        row[3] == decode(encode(row[1])+encode(action))
                                        for row in others):
                                    status = 'OBSERVED_CONFLICT'
                                    suffix = list(candidate)
                                    sources = sorted(row[0] for row in others+direct)
                                    break
                            else:
                                status, mode, output = 'RESOLVED', 'DIRECT_STABLE', [current]
                        elif observed == expected_append:
                            status, mode, output = 'RESOLVED', 'DIRECT_APPEND', [observed]
                        else:
                            status = 'NO_PATH'
                else:
                    ids = encode(current)
                    status = 'NO_PATH'
                    for length in range(len(ids), 0, -1):
                        candidate = ids[-length:]
                        matched = [row for row in rows if row[2] == action and
                                   encode(row[1])[-length:] == candidate]
                        if len({row[1] for row in matched}) < 2 or any(
                                row[3] != decode(encode(row[1])+encode(action))
                                for row in matched):
                            continue
                        status, mode = 'RESOLVED', 'SUFFIX_ENDPOINT_TRANSPORT'
                        output = [decode(ids+encode(action))]
                        suffix = list(candidate)
                        sources = sorted(row[0] for row in matched)
                        break
            else:
                direct = [row for row in observations[port]
                          if row[1] == current and row[2] == action]
                if len({row[3] for row in direct}) > 1:
                    status = 'OBSERVED_CONFLICT'
                    sources = sorted(row[0] for row in direct)
            lineage = []
            if status == 'RESOLVED':
                lineage = [dict(owner) for owner in owners]
                if output[0] != current:
                    lineage.extend({'kind': 'action', 'step': index,
                                    'position': position}
                                   for position in range(len(encode(action))))
            expected_steps.append({'before': current, 'action': action,
                                   'status': status, 'mode': mode,
                                   'output': output, 'suffix_nmu': suffix,
                                   'source_ids': sources, 'lineage': lineage})
            if status != 'RESOLVED':
                expected_result = {
                    'status': ('OBSERVATION_CONTRADICTION'
                               if status == 'OBSERVED_CONFLICT' else 'NO_PATH'),
                    'output': [], 'lineage': [], 'completed_steps': index}
                break
            current, owners = output[0], lineage
        else:
            expected_result = {'status': 'GEOMETRIC_KNOWLEDGE_SUPPORTED',
                               'output': [current], 'lineage': owners,
                               'completed_steps': len(actions)}
        return (canonical(c['steps']) == canonical(expected_steps) and
                canonical(c['result']) == canonical(expected_result))
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        return False

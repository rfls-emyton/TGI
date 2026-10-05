"""Independent replay for a source-bound one-NMU edit certificate."""
import hashlib

from .frame_engine import canonical
from .identity import REGISTRY_ID, encode, decode
from .lineage_state_check import verify_lineage_state
from .organization_snapshot import snapshot
from .phase_bound_response_atlas import PhaseBoundResponseAtlas


def _sha(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def verify_source_bound_single_nmu_edit(old, bridge, new, root_port,
                                        anchor, action, certificate):
    try:
        c = certificate
        if type(c) is not dict or set(c) != {'policy','registry','state','port',
                'event_sha256','atlas_certificate_sha256','result'} or \
           c['policy'] != 'source_bound_single_nmu_edit_v1' or c['registry'] != REGISTRY_ID or \
           type(action) is not str or not action or \
           not verify_lineage_state(old, bridge, new, root_port, anchor,
                                    [action], c['state']):
            return False
        model, groups, _ = new
        view = snapshot(model)
        seen, events, rows = set(), [], {}
        for index, group in enumerate(groups):
            if type(group) is not list or len(group) < 3:
                return False
            ports, actions = {}, set()
            for spec in group:
                if type(spec) is not dict or set(spec) != {'port','source'}:
                    return False
                port, source = spec['port'], spec['source']
                if source in seen or source not in view.episodes or port in ports or \
                   not view._alive(source):
                    return False
                seen.add(source)
                frames = view.episodes[source][0]
                if len(frames) != 3:
                    return False
                before, event_action, after = map(decode, frames)
                actions.add(event_action)
                ports[port] = [before, after]
                rows.setdefault(port, []).append((source,before,event_action,after))
            if len(actions) != 1:
                return False
            events.append({'source': f'event-{index}', 'action': actions.pop(),
                           'ports': ports})
        if seen != set(view.episodes) or _sha(events) != c['event_sha256']:
            return False
        atlas = PhaseBoundResponseAtlas(events)
        if _sha(atlas.certificate) != c['atlas_certificate_sha256'] or \
           c['port'] != c['state']['port']:
            return False
        status = c['state']['result']['status']
        if status != 'OBSERVED_STATE_READY':
            expected = {'status':status,'mode':None,'output':[],
                        'pair_nmu':[],'source_ids':[],'lineage':[]}
            return canonical(c['result']) == canonical(expected)
        seed = c['state']['result']['seed'][0]
        role = atlas.resolve(action)
        expected = {'status':'NO_PATH','mode':None,'output':[],
                    'pair_nmu':[],'source_ids':[],'lineage':[]}
        all_direct = [r for r in rows[c['port']] if r[1] == seed and r[2] == action]
        if len({r[3] for r in all_direct}) > 1:
            expected['status'] = 'OBSERVATION_CONTRADICTION'
            expected['source_ids'] = sorted(r[0] for r in all_direct)
        elif role and any(c['port'] in members for members in role):
            relevant = [r for r in rows[c['port']] if r[2] == action]
            direct = [r for r in relevant if r[1] == seed]
            outcome, pair, sources, mode = None, None, [], None
            if direct:
                sources = sorted(r[0] for r in direct)
                values = {r[3] for r in direct}
                if len(values) > 1:
                    expected['status'] = 'OBSERVATION_CONTRADICTION'
                    expected['source_ids'] = sources
                else:
                    value = next(iter(values))
                    left, right = encode(seed), encode(value)
                    changes = [i for i in range(len(left)) if len(left)==len(right)
                               and left[i] != right[i]]
                    if value == seed:
                        outcome, mode = value, 'DIRECT'
                    elif len(changes) == 1:
                        pair = (left[changes[0]], right[changes[0]])
                        outcome, mode = value, 'DIRECT'
                    else:
                        expected['source_ids'] = sources
            else:
                eligible = []
                pairs = set()
                for _, before, _, after in relevant:
                    left, right = encode(before), encode(after)
                    if len(left) != len(right):
                        continue
                    changes = [i for i,(a,b) in enumerate(zip(left,right)) if a!=b]
                    if len(changes)==1 and left.count(left[changes[0]])==1:
                        pairs.add((left[changes[0]],right[changes[0]]))
                for removed, added in pairs:
                    if encode(seed).count(removed)!=1:
                        continue
                    applicable = [r for r in relevant if encode(r[1]).count(removed)==1]
                    support = []
                    for r in applicable:
                        left,right=encode(r[1]),encode(r[3])
                        change=[i for i,(a,b) in enumerate(zip(left,right)) if a!=b]
                        if len(left)==len(right) and len(change)==1 and \
                           left[change[0]]==removed and right[change[0]]==added:
                            support.append(r)
                    if len(applicable)==len(support) and len({r[1] for r in support})>=2:
                        ids=list(encode(seed));ids[ids.index(removed)]=added
                        eligible.append(((removed,added),decode(ids),sorted(r[0] for r in support)))
                if len(eligible)==1:
                    pair,outcome,sources=eligible[0]
                    mode='HELDOUT_SUBSTITUTE'
            if outcome is not None:
                left,right=encode(seed),encode(outcome)
                lineage=[({'kind':'witness','position':i,'source_ids':sources}
                          if left[i]!=right[i] else {'kind':'seed','position':i})
                         for i in range(len(right))]
                expected={'status':'RESOLVED','mode':mode,'output':[outcome],
                          'pair_nmu':list(pair) if pair else [],
                          'source_ids':sources,'lineage':lineage}
        return canonical(c['result']) == canonical(expected)
    except (ValueError,TypeError,KeyError,IndexError,AttributeError):
        return False

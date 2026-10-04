"""Spatial action relation formed from source-owned crystal episodes."""
from hashlib import sha256
from .frame_engine import canonical
from .identity import encode,decode,REGISTRY_ID
from .organization import OMEGA_CRIT
from .organization_snapshot import snapshot
from .organization_inventory_check import verify_organization_inventory

POLICY='m1_spatial_action_relation_v1'

def form_relations(model,actions,*,max_search_steps=100000):
    if type(actions) is not list or model._dirty or not verify_organization_inventory(model,max_search_steps=max_search_steps):
        raise ValueError('Complete phase-valid organization inventory required')
    view=snapshot(model)
    by_source={}
    for record in actions:
        if type(record) is not dict or set(record)!={'source','action','port'} or type(record['source']) is not str or type(record['action']) is not str or not record['action'] or type(record['port']) is not int:
            raise ValueError('Raw source-owned action observation required')
        source=record['source']
        if source in by_source or source not in view.episodes or not view._alive(source):raise ValueError('Unique alive action source required')
        frames,receipts=view.episodes[source]
        if len(frames)!=2:raise ValueError('Before/after crystal pair required')
        before,after=map(decode,frames)
        port=record['port']
        if not 0<=port<len(before) or len(before)!=len(after) or before[port]=='.' or after[port]=='.':
            raise ValueError('Persistent observed occurrence required')
        changed=[i for i,(a,b) in enumerate(zip(before,after)) if a!=b]
        if changed!=[port]:raise ValueError('Observed port effect required')
        by_source[source]={'source':source,'action_nmu':list(encode(record['action'])),
                           'before_nmu':list(frames[0]),'after_nmu':list(frames[1]),
                           'port':port,'input_nmu':frames[0][port],'output_nmu':frames[1][port],
                           'context':[list(frames[0]),port],
                           'before_origin':list(receipts[0].origin),'after_origin':list(receipts[1].origin)}
    groups={}
    for event in by_source.values():
        key=(tuple(event['action_nmu']),event['input_nmu'])
        groups.setdefault(key,[]).append(event)
    relations=[]
    for (action_nmu,input_nmu),events in sorted(groups.items()):
        events=sorted(events,key=lambda e:e['source'])
        contexts={canonical(e['context']) for e in events}
        outputs=sorted({e['output_nmu'] for e in events})
        omega=min(len(events),len(contexts))
        status='REVOKED' if len(outputs)>1 else 'CRYSTAL' if omega>=OMEGA_CRIT else 'LIQUID'
        anchor=sha256(canonical([list(action_nmu),input_nmu]).encode()).hexdigest()
        relations.append({'anchor':anchor,'action_nmu':list(action_nmu),'input_nmu':input_nmu,
                          'output_nmu':outputs[0] if len(outputs)==1 else None,
                          'candidate_outputs':outputs,'omega_relation':omega,
                          'xi_relation':1 if status=='CRYSTAL' else 0,'status':status,
                          'support_sources':[e['source'] for e in events],
                          'context_count':len(contexts),'witnesses':events})
    return {'policy':POLICY,'registry':REGISTRY_ID,'threshold':OMEGA_CRIT,
            'source_count':len(by_source),'relations':relations}

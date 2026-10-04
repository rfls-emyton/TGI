"""Independent recomputation of source-owned M1 spatial relation certificates."""
from hashlib import sha256
from .frame_engine import canonical
from .identity import encode,REGISTRY_ID
from .organization import OMEGA_CRIT
from .organization_snapshot import snapshot
from .organization_inventory_check import verify_organization_inventory

def verify_relations(model,actions,certificate):
    try:
        if model._dirty or not verify_organization_inventory(model,max_search_steps=100000):return False
        if type(certificate) is not dict or set(certificate)!={'policy','registry','threshold','source_count','relations'} or certificate['policy']!='m1_spatial_action_relation_v1' or certificate['registry']!=REGISTRY_ID or certificate['threshold']!=OMEGA_CRIT or type(certificate['relations']) is not list:return False
        if type(actions) is not list:return False
        view=snapshot(model);records={}
        for entry in actions:
            if type(entry) is not dict or set(entry)!={'source','action','port'} or type(entry['source']) is not str or type(entry['action']) is not str or not entry['action'] or type(entry['port']) is not int:return False
            source=entry['source']
            if source in records or source not in view.episodes or not view._alive(source):return False
            frames,receipts=view.episodes[source]
            if len(frames)!=2:return False
            before,after=frames;port=entry['port']
            if not 0<=port<len(before) or len(before)!=len(after):return False
            dot=encode('.')[0]
            if before[port]==dot or after[port]==dot or [i for i,(a,b) in enumerate(zip(before,after)) if a!=b]!=[port]:return False
            records[source]=(tuple(encode(entry['action'])),before[port],after[port],before,after,port,receipts)
        if certificate['source_count']!=len(records):return False
        expected={}
        for source,(action,old,new,before,after,port,receipts) in records.items():
            expected.setdefault((action,old),[]).append((source,new,before,after,port,receipts))
        if len(certificate['relations'])!=len(expected):return False
        seen=set()
        for relation in certificate['relations']:
            if type(relation) is not dict or set(relation)!={'anchor','action_nmu','input_nmu','output_nmu','candidate_outputs','omega_relation','xi_relation','status','support_sources','context_count','witnesses'}:return False
            action=tuple(relation['action_nmu']);old=relation['input_nmu'];key=(action,old)
            if key in seen or key not in expected:return False
            seen.add(key)
            events=sorted(expected[key],key=lambda x:x[0]);outputs=sorted({e[1] for e in events});contexts={canonical([list(e[2]),e[4]]) for e in events};omega=min(len(events),len(contexts))
            status='REVOKED' if len(outputs)>1 else 'CRYSTAL' if omega>=OMEGA_CRIT else 'LIQUID'
            witnesses=[]
            for source,new,before,after,port,receipts in events:
                witnesses.append({'source':source,'action_nmu':list(action),'before_nmu':list(before),'after_nmu':list(after),'port':port,'input_nmu':old,'output_nmu':new,'context':[list(before),port],'before_origin':list(receipts[0].origin),'after_origin':list(receipts[1].origin)})
            expected_row={'anchor':sha256(canonical([list(action),old]).encode()).hexdigest(),'action_nmu':list(action),'input_nmu':old,'output_nmu':outputs[0] if len(outputs)==1 else None,'candidate_outputs':outputs,'omega_relation':omega,'xi_relation':1 if status=='CRYSTAL' else 0,'status':status,'support_sources':[e[0] for e in events],'context_count':len(contexts),'witnesses':witnesses}
            if canonical(relation)!=canonical(expected_row):return False
        return len(seen)==len(expected)
    except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

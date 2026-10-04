"""Independently verify complete windows, original occurrences and frontiers."""
from .identity import decode
from .frame_engine import canonical
from .observation_point import _validate
from .organization_snapshot import snapshot
from .role_eligibility_check import verify_role_eligibility
from .role_readout_check import _verify_role_readout_contents


def verify_role_history(model,role,history,certificate):
    try:
        point=certificate['point'];source=point['source'];stop=point['stop'];query=certificate['query']
        _validate(history,source,stop,query)
        model=snapshot(model);role=snapshot(role)
        eligibility=certificate['eligibility']
        if not verify_role_eligibility(model,role,eligibility):return False
        view=snapshot(history)
        if not view._alive(source):return False
        frames,receipts=view.episodes[source]
        sizes=sorted({len(frames)-2 for frames,_ in model.episodes.values() if len(frames)>=3})
        prefixes=[];windows=[]
        for end in range(1,stop+1):
            for size in sizes:
                if end<size:continue
                start=end-size;prefix=list(map(decode,frames[start:end]))
                if prefix not in prefixes:prefixes.append(prefix)
                occurrences=[]
                for i in range(start,end):
                    origin=receipts[i].origin;offset=sum(len(f) for f in frames[:i])
                    occurrences.append({'frame':i,'start':0,'stop':len(frames[i]),'event_span':[offset,offset+len(frames[i])],
                                        'identities':list(frames[i]),'coordinates':[list((origin[0]+j,)+origin[1:]) for j in range(len(frames[i]))]})
                windows.append({'start':start,'stop':end,'readout':prefixes.index(prefix),'occurrences':occurrences})
        readouts=certificate['readouts']
        if len(readouts)!=len(prefixes):return False
        for prefix,readout in zip(prefixes,readouts):
            if (canonical(readout['prefix'])!=canonical(prefix) or canonical(readout['eligibility'])!=canonical(eligibility)
                or not _verify_role_readout_contents(model,role,readout)):return False
        frontier={}
        for kind in ('observed','eligible','excluded','unbound'):
            latest=-1;selected=[]
            for i,w in enumerate(windows):
                r=readouts[w['readout']]['result']
                matches=bool(r['unbound_anchors']) if kind=='unbound' else query in r[kind+'_outputs']
                if not matches:continue
                if w['stop']>latest:latest=w['stop'];selected=[]
                if w['stop']==latest:selected.append(i)
            frontier[kind]=selected
        expected={'eligibility':eligibility,'point':{'source':source,'stop':stop,'event_offset':sum(len(f) for f in frames[:stop])},
                  'query':query,'readouts':readouts,'windows':windows,'frontier':frontier}
        return canonical(certificate)==canonical(expected)
    except (TypeError,ValueError,KeyError,IndexError,AttributeError):return False

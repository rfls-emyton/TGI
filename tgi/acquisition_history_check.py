"""Independent history coverage and conditional intersection verification."""
from .identity import decode
from .organization_snapshot import snapshot
from .separation_check import verify_separating_requests
from .frame_engine import canonical


def verify_acquisition_history(model,acquisition,certificate):
    try:
        if set(certificate)!={'plan','source','boundaries','events','result'}:return False
        plan=certificate['plan']
        if not verify_separating_requests(model,plan):return False
        view=snapshot(acquisition);source=certificate['source']
        if not isinstance(source,str) or not source or not view._alive(source):return False
        frames,receipts=view.episodes[source];bounds=certificate['boundaries']
        if (not isinstance(bounds,list) or len(bounds)<2 or any(type(x) is not int for x in bounds)
            or bounds[0]!=0 or bounds[-1]!=len(frames) or any(b-a<2 for a,b in zip(bounds,bounds[1:]))):return False
        if len(certificate['events'])!=len(bounds)-1:return False
        live=list(range(len(plan['contexts'])));status='OBSERVED'

        def choices(indexes):
            admitted={}
            if len(indexes)<2:return admitted
            for row in plan['requests']:
                alternatives={};covered=set()
                for g in row['responses']:
                    retained=[i for i in indexes if i in g['contexts']]
                    if retained:alternatives[tuple(g['value'])]=retained;covered.update(retained)
                if covered==set(indexes) and all(len(ids)<len(indexes) for ids in alternatives.values()):admitted[row['query']]=alternatives
            return admitted

        for step,row in enumerate(certificate['events']):
            start,stop=bounds[step:step+2];request=decode(frames[start]);observed=[decode(f) for f in frames[start+1:stop]]
            before=list(live);allowed=choices(live)
            if step==0:
                if request!=plan['request'] or observed!=plan['observed']:return False
            else:
                if request not in allowed:return False
                live=allowed[request].get(tuple(observed),[])
                status='REFINED' if live else 'UNMODELED_RESPONSE'
                if not live and step!=len(bounds)-2:return False
            occurrences=[]
            for i in range(start,stop):
                offset=sum(map(len,frames[:i]));size=len(frames[i]);origin=receipts[i].origin
                occurrences.append({'frame':i,'start':0,'stop':size,'event_span':[offset,offset+size],
                                    'identities':list(frames[i]),'coordinates':[[origin[0]+j,*origin[1:]] for j in range(size)]})
            expected={'request':request,'observed':observed,'before':before,'after':live,'admissible':sorted(allowed),'occurrences':occurrences}
            if canonical(row)!=canonical(expected):return False
        expected={'status':status,'context_indexes':live,'contexts':[plan['contexts'][i] for i in live],'next_requests':sorted(choices(live))}
        return canonical(certificate['result'])==canonical(expected)
    except (KeyError,IndexError,TypeError,ValueError,AttributeError):return False

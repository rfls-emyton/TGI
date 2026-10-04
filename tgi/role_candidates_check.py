"""Independent exhaustive pair scope and occurrence/deficit verification."""
from hashlib import sha256
from .identity import encode,decode
from .frame_engine import canonical
from .organization import _contrasts,_match,OMEGA_CRIT
from .organization_snapshot import snapshot
from .role_eligibility_check import verify_role_eligibility
from .role_work import RoleSearchBudget


def verify_role_candidates(model,role,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        try:
            model=snapshot(model);role=snapshot(role);prefix=certificate['prefix'];query=certificate['query'];eligibility=certificate['eligibility']
            if not isinstance(prefix,list) or not prefix or any(not isinstance(f,str) or not f for f in prefix):return False
            raw=tuple(map(encode,prefix));target=encode(query)
            if not target or not verify_role_eligibility(model,role,eligibility):return False
            # Direct original-prefix enumeration; no producer cache or candidate rows.
            paths=sorted({frames[:-1] for frames,_ in model.episodes.values() if len(frames)>=3});patterns=set()
            for i in range(len(paths)):
                for j in range(i+1,len(paths)):
                    budget.consume();patterns.update(_contrasts(paths[i],paths[j]))
            rows=[];admissions={row['anchor']:row['eligible'] for row in eligibility['organizations']}
            for pattern in sorted(patterns):
                budget.consume()
                if len(pattern)!=len(raw)+1:continue
                proposed=set();missing=False
                for bindings,_ in _match(pattern,raw):
                    ids=[];complete=True
                    for kind,value in pattern[-1]:
                        if kind=='lit':ids.extend(value)
                        elif value in bindings:ids.extend(bindings[value])
                        else:complete=False
                    if complete:proposed.add(tuple(ids))
                    else:missing=True
                if missing or proposed!={target}:continue
                n=1+max(v for parts in pattern for k,v in parts if k=='axis');distinct=[set() for _ in range(n)];supports=[]
                for source,(original,receipts) in sorted(model.episodes.items()):
                    budget.consume()
                    if len(original)<3 or len(original)-1!=len(pattern):continue
                    frames=original[:-1];matches=_match(pattern,frames)
                    if len(matches)!=1:continue
                    bindings,locations=matches[0];occurrences=[]
                    for axis,value in bindings.items():distinct[axis].add(value)
                    for point in sorted(locations):
                        fi=point[0];start,stop=locations[point];origin=receipts[fi].origin;offset=sum(map(len,original[:fi]))
                        occurrences.append({'frame':fi,'start':start,'stop':stop,'event_span':[offset+start,offset+stop],
                                            'identities':list(original[fi][start:stop]),'coordinates':[list((origin[0]+p,)+origin[1:]) for p in range(start,stop)]})
                    supports.append({'source':source,'bindings':[[axis,list(bindings[axis])] for axis in sorted(bindings)],'occurrences':occurrences})
                anchor=sha256(canonical(pattern).encode()).hexdigest();counts=[len(v) for v in distinct]
                phase='active' if anchor in role.organizations else 'rejected' if anchor in role.rejected_organizations else 'unformed'
                rows.append({'anchor':anchor,'pattern':pattern,'supports':supports,'values':[[decode(v) for v in sorted(a)] for a in distinct],
                             'diversity':counts,'deficit':[max(0,OMEGA_CRIT-c) for c in counts],'phase':phase,'eligible':admissions.get(anchor)})
            expected={'class':'single_contrast','eligibility':eligibility,'prefix':prefix,'query':query,'candidates':rows}
            return canonical(certificate)==canonical(expected)
        except (TypeError,ValueError,KeyError,IndexError,AttributeError):return False

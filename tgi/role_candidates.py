"""Source-bound single-contrast candidates, including unsaturated patterns."""
from hashlib import sha256
from itertools import combinations
from .identity import encode,decode
from .frame_engine import canonical
from .organization import _contrasts,_match,OMEGA_CRIT
from .organization_snapshot import snapshot
from .incidence import _endpoint
from .role_eligibility_check import verify_role_eligibility
from .role_work import RoleSearchBudget


def certify_role_candidates(model,role,eligibility,prefix,query,*,max_search_steps=None):
    if not isinstance(prefix,(list,tuple)) or not prefix or any(not isinstance(f,str) or not f for f in prefix):raise ValueError('Raw prefix required')
    raw=tuple(map(encode,prefix));target=encode(query)
    if not target:raise ValueError('Query required')
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        model=snapshot(model);role=snapshot(role)
        if not verify_role_eligibility(model,role,eligibility):raise ValueError('Invalid role evidence')
        paths=sorted({f for f,_ in role.episodes.values()});patterns=set()
        for pair in combinations(paths,2):budget.consume();patterns.update(_contrasts(*pair))
        eligible={x['anchor']:x['eligible'] for x in eligibility['organizations']};rows=[]
        for pattern in sorted(patterns):
            budget.consume()
            if len(pattern)!=len(raw)+1:continue
            outputs=set();unbound=False
            for binding,_ in _match(pattern,raw):
                if any(k=='axis' and v not in binding for k,v in pattern[-1]):unbound=True;continue
                outputs.add(tuple(x for k,v in pattern[-1] for x in (v if k=='lit' else binding[v])))
            if unbound or outputs!={target}:continue
            n=1+max(v for parts in pattern for k,v in parts if k=='axis');values=[set() for _ in range(n)];supports=[]
            for source,(frames,_) in sorted(role.episodes.items()):
                budget.consume()
                if len(frames)!=len(pattern):continue
                matches=_match(pattern,frames)
                if len(matches)!=1:continue
                binding,locations=matches[0]
                for axis,value in binding.items():values[axis].add(value)
                supports.append({'source':source,'bindings':[[axis,list(value)] for axis,value in sorted(binding.items())],
                                 'occurrences':[_endpoint(role,source,(f,start,stop)) for (f,_),(start,stop) in sorted(locations.items())]})
            anchor=sha256(canonical(pattern).encode()).hexdigest();diversity=list(map(len,values))
            rows.append({'anchor':anchor,'pattern':pattern,'supports':supports,'values':[[decode(v) for v in sorted(a)] for a in values],
                         'diversity':diversity,'deficit':[max(0,OMEGA_CRIT-d) for d in diversity],
                         'phase':'active' if anchor in role.organizations else 'rejected' if anchor in role.rejected_organizations else 'unformed',
                         'eligible':eligible.get(anchor)})
        return {'class':'single_contrast','eligibility':eligibility,'prefix':list(prefix),'query':query,'candidates':rows}

"""Complete conditional probe planning over measured candidate occurrences."""
from .identity import decode
from .frame_engine import canonical
from .organization_snapshot import snapshot
from .role_work import RoleSearchBudget
from .acquisition_witness import certify_acquisition_witness,verify_acquisition_witness
from .witness_response import _measured_root_index
from .witness_function import certify_witness_function,verify_witness_function

def certify_witness_probe(model,measurements,root,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        view=snapshot(model);w=certify_acquisition_witness(view,measurements);_measured_root_index(w['measurements'],root);rows=[];admitted=[]
        queries=sorted({decode(frames[-2]) for frames,_ in view.episodes.values() if len(frames)>=3})
        for query in queries:
            budget.consume();c=certify_witness_function(view,measurements,root,query);groups={};complete=True
            for i,b in enumerate(c['branches']):
                r=b['response']['result'];complete &= r['status'] in ('CONDITIONAL_FUNCTION','OBSERVED_RESPONSE')
                if r['output']:groups.setdefault(tuple(r['output']),[]).append(i)
            count=len(c['branches']);separates=count>1 and complete and all(len(ids)<count for ids in groups.values())
            rows.append({'query':query,'certificate':c,'groups':[{'response':list(v),'branches':ids} for v,ids in sorted(groups.items())],'separates':separates})
            if separates:admitted.append(query)
        return {'policy':'measured_probe_plan_v1','root':dict(root),'witness':w,'requests':rows,'result':{'status':'SEPARATING' if admitted else 'NO_SEPARATOR','requests':admitted}}

def verify_witness_probe(model,measurements,root,certificate,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        try:
            view=snapshot(model)
            if set(certificate)!={'policy','root','witness','requests','result'} or certificate['policy']!='measured_probe_plan_v1' or canonical(certificate['root'])!=canonical(root):return False
            w=certificate['witness']
            if not verify_acquisition_witness(view,measurements,w):return False
            _measured_root_index(w['measurements'],root)
            queries=sorted(set(decode(frames[-2]) for frames,_ in view.episodes.values() if len(frames)>=3));rows=certificate['requests']
            if not isinstance(rows,list) or len(rows)!=len(queries):return False
            admitted=[]
            for query,row in zip(queries,rows):
                budget.consume()
                if set(row)!={'query','certificate','groups','separates'} or row['query']!=query:return False
                c=row['certificate']
                if canonical(c['witness'])!=canonical(w) or not verify_witness_function(view,measurements,root,query,c):return False
                answers=[];complete=bool(c['branches'])
                for b in c['branches']:
                    r=b['response']['result'];complete &= r['status'] in ('CONDITIONAL_FUNCTION','OBSERVED_RESPONSE');answers.append(r['output'])
                values=sorted({tuple(a) for a in answers if a});groups=[{'response':list(v),'branches':[i for i,a in enumerate(answers) if tuple(a)==v]} for v in values]
                separates=len(answers)>1 and complete and len(values)>1 and all(len(g['branches'])<len(answers) for g in groups)
                if canonical(row['groups'])!=canonical(groups) or type(row['separates']) is not bool or row['separates']!=separates:return False
                if separates:admitted.append(query)
            return canonical(certificate['result'])==canonical({'status':'SEPARATING' if admitted else 'NO_SEPARATOR','requests':admitted})
        except (KeyError,IndexError,TypeError,ValueError,AttributeError):return False

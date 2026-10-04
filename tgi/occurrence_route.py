"""Geometric routing among verified equivalent observed occurrences."""
from fractions import Fraction
from .incidence import trace_incidence,verify_incidence
from .organization_snapshot import snapshot
from .momentum import select_relative_momentum
from .frame_engine import canonical

def _geometry(engine,incidence):
    origin=incidence['origin']
    if origin['stop']<2:return None
    current=tuple(origin['coordinates'][-1]);previous=(current[0]-1,)+current[1:]
    view=engine.frames.view()
    if previous not in view.atoms or current not in view.atoms or not any(b.end==current for b in view.bonds.get(previous,())):return None
    return previous,current

def _scores(rows):
    return [{'coordinate':list(p),'numerator':v.numerator,'denominator':v.denominator} for p,v in rows]

def route_occurrence(engine,source,frame,start,stop):
    if not engine._dirty:engine=snapshot(engine)
    incidence=trace_incidence(engine,source,frame,start,stop,direction='forward')
    result={'status':incidence['status'],'incidence':incidence,'previous':None,'current':None,'scores':[],'rejected':[],'selected':None}
    if incidence['status']!='LINKED':return result
    if not verify_incidence(engine,incidence):result['status']='INCOMPLETE';return result
    geometry=_geometry(engine,incidence)
    if geometry is None:result['status']='INCOMPLETE';return result
    previous,current=geometry
    decision=select_relative_momentum(previous,current,[tuple(p['coordinates'][0]) for p in incidence['targets']])
    result.update(previous=list(previous),current=list(current),scores=_scores(decision.scores),rejected=[list(p) for p in decision.rejected],status=decision.status)
    if decision.status=='NO_PATH':result['status']='NO_ROUTE'
    if decision.status=='RESOLVED':
        candidates=[p for p in incidence['targets'] if tuple(p['coordinates'][0])==decision.target]
        result['status']='ROUTED' if len(candidates)==1 else 'AMBIGUOUS'
        if len(candidates)==1:result['selected']=candidates[0]
    return result

def verify_occurrence_route(engine,result):
    try:
        if engine._dirty or result['status']!='ROUTED':return False
        engine=snapshot(engine);incidence=result['incidence']
        if incidence.get('direction')!='forward' or not verify_incidence(engine,incidence):return False
        geometry=_geometry(engine,incidence)
        if geometry is None:return False
        previous,current=geometry;momentum=tuple(a-p for p,a in zip(previous,current));scores=[];rejected=[]
        for coordinate in sorted({tuple(t['coordinates'][0]) for t in incidence['targets']}):
            delta=tuple(b-a for a,b in zip(current,coordinate));dot=sum(a*b for a,b in zip(momentum,delta))
            if dot<=0:rejected.append(list(coordinate));continue
            norm=sum(v*v for v in delta);scores.append((coordinate,Fraction(dot*dot,norm)))
        if not scores:return False
        best=max(v for _,v in scores);winners=[p for p,v in scores if v==best]
        if len(winners)!=1:return False
        selected=[t for t in incidence['targets'] if tuple(t['coordinates'][0])==winners[0]]
        if len(selected)!=1:return False
        expected={'status':'ROUTED','incidence':incidence,'previous':list(previous),'current':list(current),'scores':_scores(scores),'rejected':rejected,'selected':selected[0]}
        return canonical(result)==canonical(expected)
    except (KeyError,IndexError,ValueError,TypeError,AttributeError,ZeroDivisionError):return False

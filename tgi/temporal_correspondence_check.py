from tgi.compact_measured_path import _read_count
"""Independent temporal-gap, complete-block and reverse-path verifier."""
import copy
from .organization_snapshot import snapshot
from .organization import OMEGA_CRIT
from .compact_acquisition_map_check import verify_compact_acquisition_map
from .compact_measured_path import _decimal_count
from .role_work import RoleSearchBudget
from .frame_engine import canonical

def verify_temporal_correspondence(model,measurements,left,right,query,c,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
      try:
        fields={'policy','threshold','whole','components','blocks','edges','prefix_counts','assignment_counts','outputs','status','output'}
        if not isinstance(c,dict) or set(c)!=fields or c['policy']!='temporal_correspondence_dag_v1' or type(c['threshold']) is not int or c['threshold']!=OMEGA_CRIT:return False
        if not isinstance(measurements,list) or any(not isinstance(x,dict) for x in measurements) or not isinstance(left,list) or not isinstance(right,list):return False
        m=snapshot(model);r=[dict(x) for x in measurements];left=list(left);right=list(right)
        if not verify_compact_acquisition_map(m,r,left,right,query,c['whole']):return False
        if len({x['clock'] for x in r})!=1:
            expected=dict(components=[],blocks=[],edges=[],prefix_counts=['0'],assignment_counts=['0'],outputs=[],status='CLOCK_UNDETERMINED',output=None)
            return all(canonical(c[k])==canonical(v) for k,v in expected.items())
        ordered=sorted(r,key=lambda x:(x['lower'],x['upper'],x['source']));ends=[];maximum=None
        for i,record in enumerate(ordered):
            budget.consume();maximum=record['upper'] if maximum is None else max(maximum,record['upper'])
            if i==len(ordered)-1 or maximum<ordered[i+1]['lower']:ends.append(i+1)
        components=[];begin=0
        for end in ends:components.append([x['source'] for x in ordered[begin:end]]);begin=end
        if canonical(c['components'])!=canonical(components):return False
        count=len(components)
        if len(c['blocks'])!=count*(count+1)//2:return False
        edges=[];cursor=0
        for start in range(count):
          for stop in range(start+1,count+1):
            budget.consume();sources=sorted(s for component in components[start:stop] for s in component);row=c['blocks'][cursor]
            if set(row)!={'start','stop','sources','certificate'} or canonical({k:row[k] for k in ('start','stop','sources')})!=canonical(dict(start=start,stop=stop,sources=sources)):return False
            view=copy.copy(m);view.episodes={s:m.episodes[s] for s in sources};records=[x for x in r if x['source'] in sources];a=[s for s in left if s in sources];b=[s for s in right if s in sources];bc=row['certificate']
            if not verify_compact_acquisition_map(view,records,a,b,query,bc):return False
            if _read_count(bc['alternative_count'])>0 and bc['diversity']>=OMEGA_CRIT:edges.append(cursor)
            cursor+=1
        if canonical(c['edges'])!=canonical(edges):return False
        ways=[];assignments=[]
        for target in range(count+1):
            reverse=[0]*(target+1);weighted=[0]*(target+1);reverse[target]=1;weighted[target]=1
            for start in range(target-1,-1,-1):
                for index in edges:
                    budget.consume();b=c['blocks'][index]
                    if b['start']==start and b['stop']<=target:
                        reverse[start]+=reverse[b['stop']];weighted[start]+=weighted[b['stop']]*_read_count(b['certificate']['alternative_count'])
            ways.append(reverse[0]);assignments.append(weighted[0])
        if canonical(c['prefix_counts'])!=canonical(list(map(_decimal_count,ways))) or canonical(c['assignment_counts'])!=canonical(list(map(_decimal_count,assignments))):return False
        final=[c['blocks'][i]['certificate'] for i in edges if c['blocks'][i]['stop']==count and ways[c['blocks'][i]['start']]];outputs=sorted({x for bc in final for x in bc['outputs']});missing=any(any(o['missing'] for o in bc['outcomes']) for bc in final)
        status='UNRESOLVED' if not ways[-1] else 'UNKNOWN_ID' if missing else 'AMBIGUOUS_OUTPUT' if len(outputs)!=1 else 'CONDITIONAL_OUTPUT'
        expected=dict(outputs=outputs,status=status,output=outputs[0] if status=='CONDITIONAL_OUTPUT' else None)
        return all(canonical(c[k])==canonical(v) for k,v in expected.items())
      except (ValueError,TypeError,KeyError,IndexError,AttributeError):return False

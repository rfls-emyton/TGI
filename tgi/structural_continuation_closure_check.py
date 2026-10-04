"""Independent original-organization continuation and finite region proof check."""
from copy import deepcopy
from .identity import encode
from .frame_engine import canonical
from .observed_actuation_discovery_check import verify_observed_actuation_discovery
from .role_work import RoleSearchBudget

def _check_relation(c,command,b):
 issues=[];proofs=[];relations=[];universal=[];sources=[];b.consume()
 if c['result']['status']!='MEASURED_CONTEXT_LAW_RESOLVED':issues.append('LAW_NOT_RESOLVED')
 if c['policy']=='observation_context_laws_v1':c=c['law']
 if c.get('minimal_families')!=[[]] or len(c.get('candidates',[]))!=1:issues.append('UNCONDITIONAL_FAMILY_NOT_PROVED')
 original={row['cells'][c['root_port']]['source']:row['cells'][c['root_port']]['frames'] for row in c['rows']}
 for candidate in c.get('candidates',[]):
  b.consume();inv=candidate['inventory']
  if inv is None:issues.append('INVENTORY_MISSING');continue
  if candidate['ports']:issues.append('CONTEXT_DEPENDENCE')
  if inv['rejected']:issues.append('REVOKED_ORGANIZATIONS_PRESENT')
  if not inv['active']:issues.append('ACTIVE_ORGANIZATION_MISSING')
  for h in inv['active']:
   b.consume();frames=[]
   for frame in h['pattern']:
    parts=[]
    for kind,value in frame:
     b.consume()
     if kind=='lit':
      for scalar in value:b.consume();parts.append(['lit',scalar])
     else:parts.append([kind,value])
    frames.append(parts)
   triple=len(frames)==3;before=frames[0] if frames else [];after=frames[2] if triple else [];axes=sorted({v for k,v in before if k=='axis'});bound=axes==list(range(len(h['diversity'])));exact=triple and frames[1]==[['lit',i] for i in encode(command)];k=None
   if axes:
    count=sum(part==['axis',axes[0]] for part in before);outcount=sum(part==['axis',axes[0]] for part in after)
    if outcount%count==0:k=outcount//count
   tail=after[len(before)*k:] if k is not None else [];valid=k is not None and triple and bool(after) and after==before*k+tail and all(part[0]=='lit' for part in tail);suffix=[part[1] for part in tail] if valid else None;k=k if valid else None;unconditional=valid and exact and before==[['axis',0]] and len(h['diversity'])==1
   if not triple:issues.append('NONTRIPLE_ORGANIZATION')
   if not bound:issues.append('UNBOUND_AXIS')
   if not valid:issues.append('NONCONTINUATION_ORGANIZATION')
   if not exact:issues.append('ACTION_APPLICABILITY_NOT_EXACT')
   if valid:relations.append((k,suffix))
   if unconditional:universal.append(h['anchor'])
   proofs.append({'anchor':h['anchor'],'before_symbols':before,'action_symbols':frames[1] if triple else [],'after_symbols':after,'repeat':k,'suffix_identities':suffix,'all_axes_bound':bound,'supplies_universal_input':bool(unconditional)})
  for source in candidate['source_scope']:
   b.consume();frames=original[source];sources.append({'source':source,'before':frames[0],'action':frames[1],'after':frames[2]})
 if not universal:issues.append('UNIVERSAL_INPUT_WITNESS_MISSING')
 values={canonical(r) for r in relations};k,suffix=relations[0] if len(values)==1 else (None,None)
 if len(values)!=1:issues.append('CONTINUATION_NOT_UNIQUE')
 else:
  for source in sources:
   b.consume()
   if source['action']!=command or encode(source['before'])*k+tuple(suffix)!=encode(source['after']):issues.append('ORIGINAL_LITERAL_EXCEPTION')
 return {'status':'CONTINUATION_OBLIGATION_OPEN' if issues else 'UNIVERSAL_CONTINUATION_PROVED','issues':sorted(set(issues)),'repeat':k,'suffix_identities':suffix,'organization_proofs':proofs,'universal_input_anchors':universal,'original_sources':sources}

def verify_structural_continuation_closure(*args,goal,certificate,max_search_steps=None):
 b=RoleSearchBudget(max_search_steps)
 with b.scope():
  try:
   b.consume();c=deepcopy(certificate)
   fields={'policy','goal','discovery','continuation_laws','obligations','region_nodes','region_edges','solutions','result'}
   if type(c) is not dict or set(c)!=fields or c['policy']!='structural_continuation_closure_v1' or canonical(c['goal'])!=canonical(goal):return False
   if not verify_observed_actuation_discovery(*args,c['discovery']):return False
   d=c['discovery'];state=d['state_certificate'];ports=state['ports'];obligations=[];laws=[]
   if type(goal) is not dict or not goal or not set(goal)<=set(ports):return False
   for value in goal.values():
    if not isinstance(value,str) or not value:return False
    encode(value)
   if state['result']['status']!='JOINT_STATE_READY':obligations.append({'kind':'ACTUAL_STATE_NOT_READY'})
   if not d['result']['catalogue_current']:obligations.append({'kind':'CATALOGUE_NOT_CURRENT'})
   for item in d['laws']:
    b.consume();proof=_check_relation(item['certificate'],item['action'],b);laws.append({'action':item['action'],'port':item['port'],'proof':proof})
    if proof['status']!='UNIVERSAL_CONTINUATION_PROVED':obligations.append({'kind':'UNPROVED','action':item['action'],'port':item['port']})
   if len(laws)!=len(d['available_actions'])*len(ports):obligations.append({'kind':'COMMAND_PORT_COVERAGE_INCOMPLETE'})
   complete=not obligations;nodes=[];edges=[];solutions=[];targets=[];found=None;goal_ports=sorted(goal)
   if complete:
    goals={p:encode(goal[p]) for p in goal_ports};initial={}
    for p in goal_ports:
     ids=encode(state['state'][p]);initial[p]=len(ids) if len(ids)<=len(goals[p]) and list(ids)==list(goals[p][:len(ids)]) else None
    nodes=[{'regions':initial,'depth':0}];indices={canonical(initial):0};parents={0:[]};position=0;lookup={(l['action'],l['port']):l['proof'] for l in laws}
    while position<len(nodes):
     b.consume();source=position;node=nodes[source];position+=1
     if all(node['regions'][p]==len(goals[p]) for p in goal_ports):targets.append(source)
     for command in d['available_actions']:
      b.consume();destination={};relations={}
      for p in goal_ports:
       b.consume();law=lookup[command,p];k=law['repeat'];suffix=law['suffix_identities'];old=node['regions'][p];relations[p]={'repeat':k,'suffix_identities':deepcopy(suffix)}
       if old is None and k>0:destination[p]=None;continue
       result=[]
       for j in range(k):result.extend(goals[p][:old])
       result.extend(suffix);destination[p]=len(result) if len(result)<=len(goals[p]) and result==list(goals[p][:len(result)]) else None
      key=canonical(destination)
      if key not in indices:indices[key]=len(nodes);nodes.append({'regions':destination,'depth':node['depth']+1});parents[indices[key]]=[]
      successor=indices[key];edge=len(edges);edges.append({'source':source,'action':command,'relations':relations,'successor':successor})
      if nodes[successor]['depth']==node['depth']+1:parents[successor].append(edge)
    if targets:
     found=min(nodes[t]['depth'] for t in targets)
     for target in targets:
      if nodes[target]['depth']!=found:continue
      pending=[(target,[])]
      while pending:
       b.consume();n,reverse=pending.pop()
       if n:
        for edge in reversed(parents[n]):pending.append((edges[edge]['source'],reverse+[edge]))
       else:
        path=list(reversed(reverse));solutions.append({'goal_node':target,'edges':path,'actions':[edges[i]['action'] for i in path]})
     solutions.sort(key=lambda s:(s['actions'],s['edges']))
   status='STRUCTURAL_CLOSURE_OBLIGATION_OPEN' if not complete else 'SUPPORTED_RELATION_GOAL_REACHABLE' if found is not None else 'SUPPORTED_RELATION_GOAL_EXCLUDED'
   expected={'policy':'structural_continuation_closure_v1','goal':deepcopy(goal),'discovery':d,'continuation_laws':laws,'obligations':obligations,'region_nodes':nodes,'region_edges':edges,'solutions':solutions,'result':{'status':status,'quantified_continuation_system_complete':complete,'shortest_supported_goal_length':found,'goal_nodes':targets,'all_finite_region_obligations_exhausted':complete,'solution_count':len(solutions)}}
   return canonical(c)==canonical(expected)
  except (ValueError,KeyError,TypeError,IndexError,AttributeError):return False

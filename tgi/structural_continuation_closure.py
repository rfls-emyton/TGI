"""Source-derived repetition/constant continuation and exact finite goal closure."""
from collections import Counter
from copy import deepcopy
from .identity import encode
from .frame_engine import canonical
from .observed_actuation_discovery import certify_observed_actuation_discovery
from .role_work import RoleSearchBudget

def _symbols(parts,b):
 out=[]
 for kind,value in parts:
  b.consume()
  if kind=='lit':
   for identity in value:b.consume();out.append(['lit',identity])
  else:out.append([kind,value])
 return out

def _relation(law,action,b):
 b.consume();issues=[];proofs=[];relations=[];universal=[];sources=[]
 if law['result']['status']!='MEASURED_CONTEXT_LAW_RESOLVED':issues.append('LAW_NOT_RESOLVED')
 if law['policy']=='observation_context_laws_v1':law=law['law']
 if law.get('minimal_families')!=[[]] or len(law.get('candidates',[]))!=1:issues.append('UNCONDITIONAL_FAMILY_NOT_PROVED')
 for candidate in law.get('candidates',[]):
  b.consume();inventory=candidate['inventory']
  if inventory is None:issues.append('INVENTORY_MISSING');continue
  if candidate['ports']:issues.append('CONTEXT_DEPENDENCE')
  if inventory['rejected']:issues.append('REVOKED_ORGANIZATIONS_PRESENT')
  if not inventory['active']:issues.append('ACTIVE_ORGANIZATION_MISSING')
  for h in inventory['active']:
   b.consume();frames=[_symbols(parts,b) for parts in h['pattern']];triple=len(frames)==3;before=frames[0] if frames else [];after=frames[2] if triple else [];bc=Counter(v for k,v in before if k=='axis');ac=Counter(v for k,v in after if k=='axis');bound=set(bc)==set(range(len(h['diversity'])));exact=triple and frames[1]==[['lit',i] for i in encode(action)];ratios={ac[a]//n for a,n in bc.items() if ac[a]%n==0};valid=bool(bc) and set(ac)<=set(bc) and all(ac[a]%n==0 for a,n in bc.items()) and len(ratios)==1;repeat=next(iter(ratios)) if valid else None;tail=after[len(before)*repeat:] if valid else [];valid=valid and triple and after[:len(before)*repeat]==before*repeat and all(k=='lit' for k,v in tail) and bool(after);suffix=[v for k,v in tail] if valid else None;repeat=repeat if valid else None;all_inputs=valid and exact and before==[['axis',0]] and len(h['diversity'])==1
   if not triple:issues.append('NONTRIPLE_ORGANIZATION')
   if not bound:issues.append('UNBOUND_AXIS')
   if not valid:issues.append('NONCONTINUATION_ORGANIZATION')
   if not exact:issues.append('ACTION_APPLICABILITY_NOT_EXACT')
   if valid:relations.append((repeat,suffix))
   if all_inputs:universal.append(h['anchor'])
   proofs.append({'anchor':h['anchor'],'before_symbols':before,'action_symbols':frames[1] if triple else [],'after_symbols':after,'repeat':repeat,'suffix_identities':suffix,'all_axes_bound':bound,'supplies_universal_input':bool(all_inputs)})
  for source in candidate['source_scope']:
   b.consume();row=next(r for r in law['rows'] if r['cells'][law['root_port']]['source']==source);f=row['cells'][law['root_port']]['frames'];sources.append({'source':source,'before':f[0],'action':f[1],'after':f[2]})
 if not universal:issues.append('UNIVERSAL_INPUT_WITNESS_MISSING')
 unique=relations and all(r==relations[0] for r in relations);repeat,suffix=relations[0] if unique else (None,None)
 if not unique:issues.append('CONTINUATION_NOT_UNIQUE')
 else:
  for row in sources:
   b.consume()
   if row['action']!=action or encode(row['after'])!=encode(row['before'])*repeat+tuple(suffix):issues.append('ORIGINAL_LITERAL_EXCEPTION')
 return {'status':'UNIVERSAL_CONTINUATION_PROVED' if not issues else 'CONTINUATION_OBLIGATION_OPEN','issues':sorted(set(issues)),'repeat':repeat,'suffix_identities':suffix,'organization_proofs':proofs,'universal_input_anchors':universal,'original_sources':sources}

def _region(ids,target):return len(ids) if len(ids)<=len(target) and ids==target[:len(ids)] else None

def certify_structural_continuation_closure(*args,goal,max_search_steps=None):
 b=RoleSearchBudget(max_search_steps)
 with b.scope():
  b.consume();goal=deepcopy(goal);d=certify_observed_actuation_discovery(*args);state=d['state_certificate'];ports=state['ports']
  if type(goal) is not dict or not goal or not set(goal)<=set(ports):raise ValueError('Original nonempty port goal required')
  for value in goal.values():
   if not isinstance(value,str) or not value:raise ValueError('Original nonempty goal required')
   encode(value)
  obligations=[];laws=[]
  if state['result']['status']!='JOINT_STATE_READY':obligations.append({'kind':'ACTUAL_STATE_NOT_READY'})
  if not d['result']['catalogue_current']:obligations.append({'kind':'CATALOGUE_NOT_CURRENT'})
  for item in d['laws']:
   b.consume();proof=_relation(item['certificate'],item['action'],b);laws.append({'action':item['action'],'port':item['port'],'proof':proof})
   if proof['status']!='UNIVERSAL_CONTINUATION_PROVED':obligations.append({'kind':'UNPROVED','action':item['action'],'port':item['port']})
  if len(laws)!=len(d['available_actions'])*len(ports):obligations.append({'kind':'COMMAND_PORT_COVERAGE_INCOMPLETE'})
  complete=not obligations;nodes=[];edges=[];solutions=[];targets=[];found=None;goal_ports=sorted(goal)
  if complete:
   goals={p:encode(goal[p]) for p in goal_ports};initial={p:_region(encode(state['state'][p]),goals[p]) for p in goal_ports};nodes=[{'regions':initial,'depth':0}];known={canonical(initial):0};parents={0:[]};lookup={(l['action'],l['port']):l['proof'] for l in laws};queue=[0]
   for source in queue:
    b.consume();node=nodes[source]
    if all(node['regions'][p]==len(goals[p]) for p in goal_ports):targets.append(source)
    for action in d['available_actions']:
     b.consume();regions={};relations={}
     for p in goal_ports:
      b.consume();r=lookup[action,p];k=r['repeat'];suffix=tuple(r['suffix_identities']);i=node['regions'][p];relations[p]={'repeat':k,'suffix_identities':list(suffix)};regions[p]=None if i is None and k else _region((goals[p][:i]*k if k else ())+suffix,goals[p])
     key=canonical(regions)
     if key not in known:known[key]=len(nodes);nodes.append({'regions':regions,'depth':node['depth']+1});parents[known[key]]=[];queue.append(known[key])
     successor=known[key];index=len(edges);edges.append({'source':source,'action':action,'relations':relations,'successor':successor})
     if nodes[successor]['depth']==node['depth']+1:parents[successor].append(index)
   if targets:
    found=min(nodes[t]['depth'] for t in targets)
    for target in targets:
     if nodes[target]['depth']!=found:continue
     stack=[(target,[])]
     while stack:
      b.consume();n,reverse=stack.pop()
      if n:
       for edge in reversed(parents[n]):stack.append((edges[edge]['source'],reverse+[edge]))
      else:
       path=list(reversed(reverse));solutions.append({'goal_node':target,'edges':path,'actions':[edges[j]['action'] for j in path]})
    solutions.sort(key=lambda x:(x['actions'],x['edges']))
  status='STRUCTURAL_CLOSURE_OBLIGATION_OPEN' if not complete else 'SUPPORTED_RELATION_GOAL_REACHABLE' if found is not None else 'SUPPORTED_RELATION_GOAL_EXCLUDED'
  return {'policy':'structural_continuation_closure_v1','goal':goal,'discovery':d,'continuation_laws':laws,'obligations':obligations,'region_nodes':nodes,'region_edges':edges,'solutions':solutions,'result':{'status':status,'quantified_continuation_system_complete':complete,'shortest_supported_goal_length':found,'goal_nodes':targets,'all_finite_region_obligations_exhausted':complete,'solution_count':len(solutions)}}

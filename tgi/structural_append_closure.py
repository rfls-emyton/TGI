"""Quantified original-organization append closure and exact finite goal obligations."""
from copy import deepcopy
from .identity import encode,decode
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

def _append(law,action,b):
 b.consume();issues=[];proofs=[];suffixes=[];universal=[];source_checks=[]
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
   b.consume();frames=[_symbols(parts,b) for parts in h['pattern']];valid=len(frames)==3;before=frames[0] if frames else [];after=frames[2] if len(frames)>2 else [];tail=after[len(before):];axes=sorted({v for k,v in before if k=='axis'});bound=axes==list(range(len(h['diversity'])));copy=valid and after[:len(before)]==before and all(k=='lit' for k,v in tail);exact=valid and frames[1]==[['lit',i] for i in encode(action)];all_inputs=exact and before==[['axis',0]] and len(h['diversity'])==1
   if not valid:issues.append('NONTRIPLE_ORGANIZATION')
   if not bound:issues.append('UNBOUND_AXIS')
   if not copy:issues.append('NONAPPEND_ORGANIZATION')
   if not exact:issues.append('ACTION_APPLICABILITY_NOT_EXACT')
   suffix=[v for k,v in tail] if copy else None
   if suffix is not None:suffixes.append(suffix)
   if all_inputs and copy:universal.append(h['anchor'])
   proofs.append({'anchor':h['anchor'],'before_symbols':before,'action_symbols':frames[1] if len(frames)>1 else [],'after_symbols':after,'append_identities':suffix,'all_axes_bound':bound,'supplies_universal_input':bool(all_inputs and copy)})
  for source in candidate['source_scope']:
   b.consume();row=next(r for r in law['rows'] if r['cells'][law['root_port']]['source']==source);f=row['cells'][law['root_port']]['frames'];source_checks.append({'source':source,'before':f[0],'action':f[1],'after':f[2]})
 if not universal:issues.append('UNIVERSAL_INPUT_WITNESS_MISSING')
 if not suffixes or any(s!=suffixes[0] for s in suffixes):issues.append('SUFFIX_NOT_UNIQUE')
 suffix=suffixes[0] if suffixes and all(s==suffixes[0] for s in suffixes) else None
 if suffix is not None:
  for row in source_checks:
   b.consume()
   if row['action']!=action or encode(row['after'])!=encode(row['before'])+tuple(suffix):issues.append('ORIGINAL_LITERAL_EXCEPTION')
 return {'status':'UNIVERSAL_APPEND_RELATION_PROVED' if not issues else 'APPEND_RELATION_OBLIGATION_OPEN','issues':sorted(set(issues)),'suffix_identities':suffix,'organization_proofs':proofs,'universal_input_anchors':universal,'original_sources':source_checks}

def certify_structural_append_closure(*args,goal,max_search_steps=None):
 b=RoleSearchBudget(max_search_steps)
 with b.scope():
  b.consume();goal=deepcopy(goal);d=certify_observed_actuation_discovery(*args);state=d['state_certificate'];ports=state['ports']
  if not isinstance(goal,dict) or not goal or not set(goal)<=set(ports):raise ValueError('Original nonempty port goal required')
  for value in goal.values():
   if not isinstance(value,str) or not value:raise ValueError('Original nonempty goal frame required')
   encode(value)
  obligations=[];laws=[]
  if state['result']['status']!='JOINT_STATE_READY':obligations.append('ACTUAL_STATE_NOT_READY')
  if not d['result']['catalogue_current']:obligations.append('CATALOGUE_NOT_CURRENT')
  for item in d['laws']:
   b.consume();proof=_append(item['certificate'],item['action'],b);laws.append({'action':item['action'],'port':item['port'],'proof':proof})
   if proof['status']!='UNIVERSAL_APPEND_RELATION_PROVED':obligations.append('UNPROVED:'+item['action']+':'+item['port'])
  if len(laws)!=len(d['available_actions'])*len(ports):obligations.append('COMMAND_PORT_COVERAGE_INCOMPLETE')
  complete=not obligations;obstructions=[];nodes=[];edges=[];solutions=[];found=None;targets=[];goal_ports=sorted(goal);parents={}
  if complete:
   for p in goal_ports:
    b.consume();before=encode(state['state'][p]);target=encode(goal[p])
    if len(before)>len(target) or before!=target[:len(before)]:obstructions.append({'port':p,'before_identities':list(before),'goal_identities':list(target)})
   if not obstructions:
    initial={p:len(encode(state['state'][p])) for p in goal_ports};nodes=[{'offsets':initial,'depth':0}];known={canonical(initial):0};parents={0:[]};queue=[0];lookup={(l['action'],l['port']):l['proof']['suffix_identities'] for l in laws}
    for source in queue:
     b.consume();node=nodes[source]
     if all(node['offsets'][p]==len(encode(goal[p])) for p in goal_ports):targets.append(source)
     for action in d['available_actions']:
      b.consume();offsets={};fail=[];suffixes={p:deepcopy(lookup[action,p]) for p in goal_ports}
      for p in goal_ports:
       b.consume();i=node['offsets'][p];suffix=suffixes[p];target=encode(goal[p]);offsets[p]=i+len(suffix)
       if offsets[p]>len(target) or tuple(suffix)!=target[i:offsets[p]]:fail.append(p)
      successor=None;kind='GOAL_PREFIX_REJECTED' if fail else 'ZERO_GOAL_PROGRESS' if offsets==node['offsets'] else 'GOAL_PREFIX_PROGRESS'
      if not fail:
       key=canonical(offsets)
       if key not in known:known[key]=len(nodes);nodes.append({'offsets':offsets,'depth':node['depth']+1});parents[known[key]]=[];queue.append(known[key])
       successor=known[key]
      index=len(edges);edges.append({'source':source,'action':action,'suffixes':suffixes,'failed_ports':fail,'kind':kind,'successor':successor})
      if successor is not None and kind=='GOAL_PREFIX_PROGRESS' and nodes[successor]['depth']==node['depth']+1:parents[successor].append(index)
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
  return {'policy':'structural_append_closure_v1','goal':goal,'discovery':d,'append_laws':laws,'obligations':obligations,'initial_obstructions':obstructions,'prefix_nodes':nodes,'prefix_edges':edges,'solutions':solutions,'result':{'status':status,'quantified_append_system_complete':complete,'shortest_supported_goal_length':found,'goal_nodes':targets,'all_finite_prefix_obligations_exhausted':complete,'solution_count':len(solutions)}}

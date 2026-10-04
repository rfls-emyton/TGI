"""Independent universal applicability, source completeness and finite prefix closure."""
from copy import deepcopy
from .identity import encode
from .frame_engine import canonical
from .observed_actuation_discovery_check import verify_observed_actuation_discovery
from .role_work import RoleSearchBudget

def _check_append(c,command,budget):
 issues=[];proofs=[];suffixes=[];universal=[];sources=[];budget.consume()
 if c['result']['status']!='MEASURED_CONTEXT_LAW_RESOLVED':issues.append('LAW_NOT_RESOLVED')
 if c['policy']=='observation_context_laws_v1':c=c['law']
 if c.get('minimal_families')!=[[]] or len(c.get('candidates',[]))!=1:issues.append('UNCONDITIONAL_FAMILY_NOT_PROVED')
 original={}
 for row in c['rows']:original.setdefault(row['cells'][c['root_port']]['source'],row['cells'][c['root_port']]['frames'])
 for candidate in c.get('candidates',[]):
  budget.consume();inv=candidate['inventory']
  if inv is None:issues.append('INVENTORY_MISSING');continue
  if candidate['ports']:issues.append('CONTEXT_DEPENDENCE')
  if inv['rejected']:issues.append('REVOKED_ORGANIZATIONS_PRESENT')
  if not inv['active']:issues.append('ACTIVE_ORGANIZATION_MISSING')
  for organization in inv['active']:
   budget.consume();frames=[]
   for frame in organization['pattern']:
    parts=[]
    for kind,value in frame:
     budget.consume()
     if kind=='lit':
      for scalar in value:budget.consume();parts.append(['lit',scalar])
     else:parts.append([kind,value])
    frames.append(parts)
   before=frames[0] if frames else [];after=frames[2] if len(frames)>2 else [];axes={value for kind,value in before if kind=='axis'};bound=axes==set(range(len(organization['diversity'])));triple=len(frames)==3;exact=triple and frames[1]==[['lit',scalar] for scalar in encode(command)];copied=triple and len(after)>=len(before) and all(before[i]==after[i] for i in range(len(before)));tail=after[len(before):];copied=copied and all(part[0]=='lit' for part in tail);unconditional=copied and exact and len(organization['diversity'])==1 and len(before)==1 and before[0]==['axis',0];suffix=[part[1] for part in tail] if copied else None
   if not triple:issues.append('NONTRIPLE_ORGANIZATION')
   if not bound:issues.append('UNBOUND_AXIS')
   if not copied:issues.append('NONAPPEND_ORGANIZATION')
   if not exact:issues.append('ACTION_APPLICABILITY_NOT_EXACT')
   if suffix is not None:suffixes.append(suffix)
   if unconditional:universal.append(organization['anchor'])
   proofs.append({'anchor':organization['anchor'],'before_symbols':before,'action_symbols':frames[1] if len(frames)>1 else [],'after_symbols':after,'append_identities':suffix,'all_axes_bound':bound,'supplies_universal_input':bool(unconditional)})
  for source in candidate['source_scope']:
   budget.consume();frames=original[source];sources.append({'source':source,'before':frames[0],'action':frames[1],'after':frames[2]})
 if not universal:issues.append('UNIVERSAL_INPUT_WITNESS_MISSING')
 unique={canonical(s) for s in suffixes};suffix=suffixes[0] if len(unique)==1 else None
 if suffix is None:issues.append('SUFFIX_NOT_UNIQUE')
 else:
  for source in sources:
   budget.consume()
   if source['action']!=command or tuple(encode(source['before']))+tuple(suffix)!=encode(source['after']):issues.append('ORIGINAL_LITERAL_EXCEPTION')
 return {'status':'APPEND_RELATION_OBLIGATION_OPEN' if issues else 'UNIVERSAL_APPEND_RELATION_PROVED','issues':sorted(set(issues)),'suffix_identities':suffix,'organization_proofs':proofs,'universal_input_anchors':universal,'original_sources':sources}

def verify_structural_append_closure(*args,goal,certificate,max_search_steps=None):
 b=RoleSearchBudget(max_search_steps)
 with b.scope():
  try:
   b.consume();c=deepcopy(certificate)
   if type(c) is not dict or set(c)!={'policy','goal','discovery','append_laws','obligations','initial_obstructions','prefix_nodes','prefix_edges','solutions','result'} or c['policy']!='structural_append_closure_v1' or canonical(c['goal'])!=canonical(goal):return False
   if not verify_observed_actuation_discovery(*args,c['discovery']):return False
   d=c['discovery'];state=d['state_certificate'];ports=state['ports'];obligations=[];laws=[]
   if type(goal) is not dict or not goal or not set(goal)<=set(ports):return False
   for value in goal.values():
    if not isinstance(value,str) or not value:return False
    encode(value)
   if state['result']['status']!='JOINT_STATE_READY':obligations.append('ACTUAL_STATE_NOT_READY')
   if not d['result']['catalogue_current']:obligations.append('CATALOGUE_NOT_CURRENT')
   for item in d['laws']:
    b.consume();proof=_check_append(item['certificate'],item['action'],b);laws.append({'action':item['action'],'port':item['port'],'proof':proof})
    if proof['status']!='UNIVERSAL_APPEND_RELATION_PROVED':obligations.append('UNPROVED:'+item['action']+':'+item['port'])
   if len(laws)!=len(d['available_actions'])*len(ports):obligations.append('COMMAND_PORT_COVERAGE_INCOMPLETE')
   complete=not obligations;obstructions=[];nodes=[];edges=[];solutions=[];targets=[];found=None;goal_ports=sorted(goal)
   if complete:
    goal_ids={p:encode(goal[p]) for p in goal_ports}
    for port in goal_ports:
     b.consume();ids=encode(state['state'][port])
     if len(ids)>len(goal_ids[port]) or any(i!=j for i,j in zip(ids,goal_ids[port])):obstructions.append({'port':port,'before_identities':list(ids),'goal_identities':list(goal_ids[port])})
    if not obstructions:
     offsets={p:len(encode(state['state'][p])) for p in goal_ports};nodes=[{'offsets':offsets,'depth':0}];indices={canonical(offsets):0};parents={0:[]};position=0;append={(row['action'],row['port']):row['proof']['suffix_identities'] for row in laws}
     while position<len(nodes):
      b.consume();source=position;node=nodes[position];position+=1
      if all(node['offsets'][p]==len(goal_ids[p]) for p in goal_ports):targets.append(source)
      for command in d['available_actions']:
       b.consume();suffixes={p:deepcopy(append[command,p]) for p in goal_ports};destination={};failed=[]
       for p in goal_ports:
        b.consume();start=node['offsets'][p];destination[p]=start+len(suffixes[p])
        if destination[p]>len(goal_ids[p]) or list(goal_ids[p][start:destination[p]])!=suffixes[p]:failed.append(p)
       kind='GOAL_PREFIX_REJECTED' if failed else 'ZERO_GOAL_PROGRESS' if destination==node['offsets'] else 'GOAL_PREFIX_PROGRESS';successor=None
       if not failed:
        key=canonical(destination)
        if key not in indices:indices[key]=len(nodes);nodes.append({'offsets':destination,'depth':node['depth']+1});parents[indices[key]]=[]
        successor=indices[key]
       edge=len(edges);edges.append({'source':source,'action':command,'suffixes':suffixes,'failed_ports':failed,'kind':kind,'successor':successor})
       if successor is not None and kind=='GOAL_PREFIX_PROGRESS' and nodes[successor]['depth']==node['depth']+1:parents[successor].append(edge)
     if targets:
      found=min(nodes[target]['depth'] for target in targets)
      for target in targets:
       if nodes[target]['depth']!=found:continue
       paths=[(target,[])]
       while paths:
        b.consume();node,reverse=paths.pop()
        if node:
         for edge in reversed(parents[node]):paths.append((edges[edge]['source'],reverse+[edge]))
        else:
         ordered=list(reversed(reverse));solutions.append({'goal_node':target,'edges':ordered,'actions':[edges[j]['action'] for j in ordered]})
      solutions.sort(key=lambda s:(s['actions'],s['edges']))
   status='STRUCTURAL_CLOSURE_OBLIGATION_OPEN' if not complete else 'SUPPORTED_RELATION_GOAL_REACHABLE' if found is not None else 'SUPPORTED_RELATION_GOAL_EXCLUDED'
   expected={'policy':'structural_append_closure_v1','goal':deepcopy(goal),'discovery':d,'append_laws':laws,'obligations':obligations,'initial_obstructions':obstructions,'prefix_nodes':nodes,'prefix_edges':edges,'solutions':solutions,'result':{'status':status,'quantified_append_system_complete':complete,'shortest_supported_goal_length':found,'goal_nodes':targets,'all_finite_prefix_obligations_exhausted':complete,'solution_count':len(solutions)}}
   return canonical(c)==canonical(expected)
  except (ValueError,KeyError,TypeError,IndexError,AttributeError):return False

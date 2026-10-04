"""Original measured context guards, whole-word composition and finite goal congruence."""
from copy import deepcopy
from .identity import encode
from .frame_engine import canonical
from .observed_actuation_discovery import certify_observed_actuation_discovery
from .measured_context_laws import certify_measured_context_laws
from .role_work import RoleSearchBudget

def _child(c):return c['law'] if c['policy']=='observation_context_laws_v1' else c

def _symbols(parts,b):
 out=[]
 for kind,value in parts:
  b.consume()
  if kind=='lit':
   for identity in value:b.consume();out.append(['lit',identity])
  else:out.append([kind,value])
 return out

def _expand(operator,before):
 out=[]
 for kind,value in operator:
  if kind=='before':out.extend(before)
  else:out.append(value)
 return out

def _operator(c,candidate,action,b):
 issues=[];patterns=[];universal=[];operators=[];sources=[];b.consume();inv=candidate['inventory']
 if inv is None:issues.append('INVENTORY_MISSING')
 else:
  if inv['rejected']:issues.append('REVOKED_ORGANIZATIONS_PRESENT')
  if not inv['active']:issues.append('ACTIVE_ORGANIZATION_MISSING')
  for h in inv['active']:
   b.consume();frames=[_symbols(parts,b) for parts in h['pattern']];triple=len(frames)==3;before=frames[0] if frames else [];after=frames[2] if triple else [];bound=sorted({v for k,v in before if k=='axis'})==list(range(len(h['diversity'])));exact=triple and frames[1]==[['lit',i] for i in encode(action)];whole=exact and before==[['axis',0]] and len(h['diversity'])==1 and all(k=='lit' or (k=='axis' and v==0) for k,v in after) and bool(after)
   if not triple:issues.append('NONTRIPLE_ORGANIZATION')
   if not bound:issues.append('UNBOUND_AXIS')
   if not exact:issues.append('ACTION_APPLICABILITY_NOT_EXACT')
   if whole:universal.append(h['anchor']);operators.append([['before',0] if k=='axis' else ['lit',v] for k,v in after])
   patterns.append({'anchor':h['anchor'],'before_symbols':before,'action_symbols':frames[1] if triple else [],'after_symbols':after,'all_axes_bound':bound,'supplies_universal_input':bool(whole)})
 unique=operators and all(op==operators[0] for op in operators);operator=operators[0] if unique else None
 if not universal:issues.append('UNIVERSAL_INPUT_WITNESS_MISSING')
 if not unique:issues.append('OPERATOR_NOT_UNIQUE')
 if operator is not None:
  for h in patterns:
   b.consume();expected=[]
   for k,v in operator:expected.extend(h['before_symbols'] if k=='before' else [['lit',v]])
   if expected!=h['after_symbols']:issues.append('NONWORD_ORGANIZATION')
 rows={row['cells'][c['root_port']]['source']:row['cells'][c['root_port']]['frames'] for row in c['rows']}
 for source in candidate['source_scope']:
  b.consume();frames=rows[source];sources.append({'source':source,'before':frames[0],'action':frames[1],'after':frames[2]})
  if operator is not None and (frames[1]!=action or _expand(operator,encode(frames[0]))!=list(encode(frames[2]))):issues.append('ORIGINAL_LITERAL_EXCEPTION')
 return {'status':'UNIVERSAL_WORD_OPERATOR_PROVED' if not issues else 'WORD_OPERATOR_OBLIGATION_OPEN','operator':operator,'issues':sorted(set(issues)),'organization_proofs':patterns,'universal_input_anchors':universal,'original_sources':sources}

def _transition(regions,action,ports,rules,dictionary,index,b):
 output={};proofs=[];issues=[]
 for port in ports:
  b.consume();law=rules[action,port];family_values=[];family_proofs=[];before=regions[port]
  for family in law['families']:
   b.consume();selected=family['ports'];guard={p:dictionary[regions[p]] if regions[p] is not None else None for p in selected};variant=next((v for v in family['variants'] if all(guard[p]==list(encode(v['guard'][p])) for p in selected)),None)
   if variant is None:issues.append({'kind':'CONTEXT_GUARD_UNPROVED','port':port,'family':selected});continue
   operator=variant['operator_proof']['operator'] if variant['operator_proof']['status']=='UNIVERSAL_WORD_OPERATOR_PROVED' else None;case=None;ids=None
   if operator is not None:
    if before is not None:ids=_expand(operator,dictionary[before])
   elif before is not None:
    case=next((c for c in variant['literal_cases'] if list(encode(c['before']))==dictionary[before] and c['after'] is not None),None)
    if case is not None:ids=list(encode(case['after']))
   if operator is None and case is None:issues.append({'kind':'WHOLE_BEFORE_UNPROVED','port':port,'family':selected});continue
   family_values.append(('word',ids) if before is not None else ('operator',operator));family_proofs.append({'ports':selected,'guard':deepcopy(variant['guard']),'variant_query':variant['query'],'operator':deepcopy(operator),'literal_case_query':case['query'] if case else None})
  if len(family_values)!=len(law['families']) or not family_values:continue
  if any(v!=family_values[0] for v in family_values):issues.append({'kind':'MINIMAL_FAMILY_DISAGREEMENT','port':port});continue
  kind,value=family_values[0]
  if kind=='word':output[port]=index.get(tuple(value))
  elif any(k=='before' for k,v in value):output[port]=None
  else:output[port]=index.get(tuple(v for k,v in value))
  proofs.append({'port':port,'families':family_proofs,'output_region':output[port]})
 return output,proofs,issues

def certify_guarded_word_closure(*args,goal,max_search_steps=None):
 b=RoleSearchBudget(max_search_steps)
 with b.scope():
  b.consume();goal=deepcopy(goal);d=certify_observed_actuation_discovery(*args);state=d['state_certificate'];ports=state['ports']
  if type(goal) is not dict or not goal or not set(goal)<=set(ports):raise ValueError('Original nonempty port goal required')
  for value in goal.values():
   if not isinstance(value,str) or not value:raise ValueError('Nonempty raw goal required')
   encode(value)
  queries=[];query_keys={};rules=[];base_issues=[];guard_words=set()
  def query(root,before,action,context):
   b.consume();q={'root_port':root,'before':before,'action':action,'context':deepcopy(context)};key=canonical(q)
   if key not in query_keys:
    query_keys[key]=len(queries);queries.append({**q,'certificate':certify_measured_context_laws(*args[:3],root,before,action,context)})
   return query_keys[key]
  if state['result']['status']!='JOINT_STATE_READY':base_issues.append({'kind':'ACTUAL_STATE_NOT_READY'})
  if not d['result']['catalogue_current']:base_issues.append({'kind':'CATALOGUE_NOT_CURRENT'})
  for item in d['laws']:
   b.consume();root=item['port'];action=item['action'];c=_child(item['certificate']);families=[]
   for row in c['rows']:
    if row['cells'][root]['frames'][1]==action:
     guard_words.update(cell['frames'][0] for cell in row['cells'].values())
   for selected in c['minimal_families']:
    variants=[];guards={}
    for row in c['rows']:
     b.consume()
     if row['cells'][root]['frames'][1]!=action:continue
     guard={p:row['cells'][p]['frames'][0] for p in selected};guards.setdefault(canonical(guard),(guard,row))
    for key,(guard,row) in sorted(guards.items()):
     context={p:state['state'][p] for p in ports if p!=root};context.update({p:cell['frames'][0] for p,cell in row['cells'].items() if p!=root});qi=query(root,state['state'][root],action,context);law=_child(queries[qi]['certificate']);ci=next(i for i,candidate in enumerate(law['candidates']) if candidate['ports']==selected);candidate=law['candidates'][ci];proof=_operator(law,candidate,action,b);cases=[]
     if proof['status']!='UNIVERSAL_WORD_OPERATOR_PROVED':
      rows={r['cells'][root]['source']:r['cells'][root]['frames'] for r in law['rows']};befores=sorted({rows[s][0] for s in candidate['source_scope']})
      for before in befores:
       b.consume();li=query(root,before,action,context);lc=_child(queries[li]['certificate']);lci=next(i for i,cand in enumerate(lc['candidates']) if cand['ports']==selected);literal=lc['candidates'][lci];after=literal['conclusions'][0][0] if literal['resolved'] and len(literal['conclusions'])==1 and len(literal['conclusions'][0])==1 else None;cases.append({'before':before,'after':after,'query':li,'candidate_index':lci})
     variants.append({'guard':guard,'query':qi,'candidate_index':ci,'operator_proof':proof,'literal_cases':cases})
    families.append({'ports':deepcopy(selected),'variants':variants})
   rules.append({'action':action,'port':root,'families':families})
  if len(rules)!=len(d['available_actions'])*len(ports):base_issues.append({'kind':'COMMAND_PORT_COVERAGE_INCOMPLETE'})
  words=set()
  for text in sorted(guard_words|set(goal.values())):
   ids=encode(text)
   for start in range(len(ids)):
    for stop in range(start+1,len(ids)+1):b.consume();words.add(ids[start:stop])
  dictionary=[list(w) for w in sorted(words)];index={tuple(w):i for i,w in enumerate(dictionary)};nodes=[];edges=[];obligations=deepcopy(base_issues);solutions=[];targets=[];covered_distance=None;parents={}
  if not base_issues:
   initial={p:index.get(encode(state['state'][p])) for p in ports};nodes=[{'regions':initial,'depth':0}];known={canonical(initial):0};queue=[0];parents={0:[]};lookup={(r['action'],r['port']):r for r in rules}
   for source in queue:
    b.consume();node=nodes[source]
    if all(node['regions'][p]==index[encode(goal[p])] for p in goal):targets.append(source)
    for action in d['available_actions']:
     b.consume();destination,proofs,issues=_transition(node['regions'],action,ports,lookup,dictionary,index,b);successor=None
     if not issues:
      key=canonical(destination)
      if key not in known:known[key]=len(nodes);nodes.append({'regions':destination,'depth':node['depth']+1});parents[known[key]]=[];queue.append(known[key])
      successor=known[key]
     edge=len(edges);edges.append({'source':source,'action':action,'port_proofs':proofs,'issues':issues,'successor':successor})
     obligations.extend({'node':source,'action':action,**issue} for issue in issues)
     if successor is not None and nodes[successor]['depth']==node['depth']+1:parents[successor].append(edge)
   if targets:
    covered_distance=min(nodes[t]['depth'] for t in targets)
    for target in targets:
     if nodes[target]['depth']!=covered_distance:continue
     pending=[(target,[])]
     while pending:
      b.consume();n,reverse=pending.pop()
      if n:
       for edge in reversed(parents[n]):pending.append((edges[edge]['source'],reverse+[edge]))
      else:
       path=list(reversed(reverse));solutions.append({'goal_node':target,'edges':path,'actions':[edges[e]['action'] for e in path]})
    solutions.sort(key=lambda s:(s['actions'],s['edges']))
  complete=not obligations;status='STRUCTURAL_CLOSURE_OBLIGATION_OPEN' if not complete else 'SUPPORTED_RELATION_GOAL_REACHABLE' if covered_distance is not None else 'SUPPORTED_RELATION_GOAL_EXCLUDED'
  return {'policy':'guarded_word_closure_v1','goal':goal,'discovery':d,'queries':queries,'guarded_laws':rules,'word_dictionary':dictionary,'region_nodes':nodes,'region_edges':edges,'obligations':obligations,'solutions':solutions,'result':{'status':status,'quantified_guarded_word_system_complete':complete,'shortest_supported_goal_length':covered_distance if complete else None,'shortest_covered_goal_length':covered_distance,'goal_nodes':targets,'all_finite_region_obligations_exhausted':complete,'solution_count':len(solutions)}}

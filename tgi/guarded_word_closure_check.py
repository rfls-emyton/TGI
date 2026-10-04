"""Independent guards, source-scoped word operators and exact finite relation verification."""
from copy import deepcopy
from .identity import encode
from .frame_engine import canonical
from .observed_actuation_discovery_check import verify_observed_actuation_discovery
from .measured_context_laws_check import verify_measured_context_laws
from .role_work import RoleSearchBudget

def _child(c):return c['law'] if c['policy']=='observation_context_laws_v1' else c

def _check_operator(c,candidate,action,b):
 issues=[];patterns=[];universal=[];operators=[];sources=[];b.consume();inv=candidate['inventory']
 if inv is None:issues.append('INVENTORY_MISSING')
 else:
  if inv['rejected']:issues.append('REVOKED_ORGANIZATIONS_PRESENT')
  if not inv['active']:issues.append('ACTIVE_ORGANIZATION_MISSING')
  for organization in inv['active']:
   b.consume();frames=[]
   for frame in organization['pattern']:
    output=[]
    for kind,value in frame:
     b.consume()
     if kind=='lit':
      for identity in value:b.consume();output.append(['lit',identity])
     else:output.append([kind,value])
    frames.append(output)
   triple=len(frames)==3;before=frames[0] if frames else [];after=frames[2] if triple else [];axes={part[1] for part in before if part[0]=='axis'};bound=axes==set(range(len(organization['diversity'])));exact=triple and frames[1]==[['lit',identity] for identity in encode(action)];whole=exact and len(before)==1 and before[0]==['axis',0] and len(organization['diversity'])==1 and bool(after) and all(part[0]=='lit' or part==['axis',0] for part in after)
   if not triple:issues.append('NONTRIPLE_ORGANIZATION')
   if not bound:issues.append('UNBOUND_AXIS')
   if not exact:issues.append('ACTION_APPLICABILITY_NOT_EXACT')
   if whole:
    universal.append(organization['anchor']);operators.append([['before',0] if part==['axis',0] else deepcopy(part) for part in after])
   patterns.append({'anchor':organization['anchor'],'before_symbols':before,'action_symbols':frames[1] if triple else [],'after_symbols':after,'all_axes_bound':bound,'supplies_universal_input':bool(whole)})
 values={canonical(op) for op in operators};operator=operators[0] if len(values)==1 else None
 if not universal:issues.append('UNIVERSAL_INPUT_WITNESS_MISSING')
 if len(values)!=1:issues.append('OPERATOR_NOT_UNIQUE')
 if operator is not None:
  for pattern in patterns:
   b.consume();expanded=[]
   for part in operator:
    if part[0]=='before':expanded+=pattern['before_symbols']
    else:expanded.append(deepcopy(part))
   if expanded!=pattern['after_symbols']:issues.append('NONWORD_ORGANIZATION')
 original={row['cells'][c['root_port']]['source']:row['cells'][c['root_port']]['frames'] for row in c['rows']}
 for source in candidate['source_scope']:
  b.consume();f=original[source];sources.append({'source':source,'before':f[0],'action':f[1],'after':f[2]})
  if operator is not None:
   expected=[]
   for part in operator:expected.extend(encode(f[0]) if part[0]=='before' else [part[1]])
   if f[1]!=action or expected!=list(encode(f[2])):issues.append('ORIGINAL_LITERAL_EXCEPTION')
 return {'status':'WORD_OPERATOR_OBLIGATION_OPEN' if issues else 'UNIVERSAL_WORD_OPERATOR_PROVED','operator':operator,'issues':sorted(set(issues)),'organization_proofs':patterns,'universal_input_anchors':universal,'original_sources':sources}

def _checked_step(regions,action,ports,rules,dictionary,index,b):
 destination={};proofs=[];issues=[]
 for root in ports:
  b.consume();families=rules[action,root]['families'];values=[];records=[];before=regions[root]
  for family in families:
   b.consume();selected=family['ports'];variant=None
   for v in family['variants']:
    if all(regions[p] is not None and tuple(dictionary[regions[p]])==encode(v['guard'][p]) for p in selected):variant=v;break
   if variant is None:issues.append({'kind':'CONTEXT_GUARD_UNPROVED','port':root,'family':selected});continue
   proof=variant['operator_proof'];operator=proof['operator'] if proof['status']=='UNIVERSAL_WORD_OPERATOR_PROVED' else None;literal=None;result=None
   if operator is None:
    if before is not None:
     for case in variant['literal_cases']:
      if case['after'] is not None and encode(case['before'])==tuple(dictionary[before]):literal=case;result=list(encode(case['after']));break
    if literal is None:issues.append({'kind':'WHOLE_BEFORE_UNPROVED','port':root,'family':selected});continue
   elif before is not None:
    result=[]
    for kind,value in operator:
     if kind=='before':result.extend(dictionary[before])
     else:result.append(value)
   values.append(('word',result) if before is not None else ('operator',operator));records.append({'ports':selected,'guard':deepcopy(variant['guard']),'variant_query':variant['query'],'operator':deepcopy(operator),'literal_case_query':literal['query'] if literal else None})
  if not values or len(values)!=len(families):continue
  if len({canonical(v) for v in values})!=1:issues.append({'kind':'MINIMAL_FAMILY_DISAGREEMENT','port':root});continue
  kind,value=values[0]
  if kind=='word':destination[root]=index.get(tuple(value))
  elif any(part[0]=='before' for part in value):destination[root]=None
  else:destination[root]=index.get(tuple(part[1] for part in value))
  proofs.append({'port':root,'families':records,'output_region':destination[root]})
 return destination,proofs,issues
def verify_guarded_word_closure(*args,goal,certificate,max_search_steps=None):
 b=RoleSearchBudget(max_search_steps)
 with b.scope():
  try:
   b.consume();cert=deepcopy(certificate)
   fields={'policy','goal','discovery','queries','guarded_laws','word_dictionary','region_nodes','region_edges','obligations','solutions','result'}
   if type(cert) is not dict or set(cert)!=fields or cert['policy']!='guarded_word_closure_v1' or canonical(cert['goal'])!=canonical(goal):return False
   if not verify_observed_actuation_discovery(*args,cert['discovery']):return False
   goal=deepcopy(goal);d=cert['discovery'];state=d['state_certificate'];ports=state['ports'];supplied=cert['queries'];available={}
   if type(supplied) is not list:return False
   for ordinal,q in enumerate(supplied):
    b.consume()
    if type(q) is not dict or set(q)!={'root_port','before','action','context','certificate'}:return False
    key=canonical({k:v for k,v in q.items() if k!='certificate'})
    if key in available or not verify_measured_context_laws(*args[:3],q['root_port'],q['before'],q['action'],q['context'],q['certificate']):return False
    available[key]=ordinal
   if type(goal) is not dict or not goal or not set(goal)<=set(ports):return False
   for value in goal.values():
    if not isinstance(value,str) or not value:return False
    encode(value)
   queries=[];query_keys={};rules=[];base_issues=[];guard_words=set()
   def query(root,before,action,context):
    b.consume();q={'root_port':root,'before':before,'action':action,'context':deepcopy(context)};key=canonical(q)
    if key not in query_keys:
     if key not in available:raise ValueError('Missing original query')
     original=available[key]
     if original!=len(queries):raise ValueError('Query pool order or unused query')
     query_keys[key]=len(queries);queries.append(deepcopy(supplied[original]))
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
      context={p:state['state'][p] for p in ports if p!=root};context.update({p:cell['frames'][0] for p,cell in row['cells'].items() if p!=root});qi=query(root,state['state'][root],action,context);law=_child(queries[qi]['certificate']);ci=next(i for i,candidate in enumerate(law['candidates']) if candidate['ports']==selected);candidate=law['candidates'][ci];proof=_check_operator(law,candidate,action,b);cases=[]
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
    initial={p:index.get(encode(state['state'][p])) for p in ports};nodes=[{'regions':initial,'depth':0}];known={canonical(initial):0};cursor=0;parents={0:[]};lookup={(r['action'],r['port']):r for r in rules}
    while cursor<len(nodes):
     b.consume();source=cursor;node=nodes[cursor];cursor+=1
     if all(node['regions'][p]==index[encode(goal[p])] for p in goal):targets.append(source)
     for action in d['available_actions']:
      b.consume();destination,proofs,issues=_checked_step(node['regions'],action,ports,lookup,dictionary,index,b);successor=None
      if not issues:
       key=canonical(destination)
       if key not in known:known[key]=len(nodes);nodes.append({'regions':destination,'depth':node['depth']+1});parents[known[key]]=[]
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
   if len(queries)!=len(supplied):return False
   expected={'policy':'guarded_word_closure_v1','goal':goal,'discovery':d,'queries':queries,'guarded_laws':rules,'word_dictionary':dictionary,'region_nodes':nodes,'region_edges':edges,'obligations':obligations,'solutions':solutions,'result':{'status':status,'quantified_guarded_word_system_complete':complete,'shortest_supported_goal_length':covered_distance if complete else None,'shortest_covered_goal_length':covered_distance,'goal_nodes':targets,'all_finite_region_obligations_exhausted':complete,'solution_count':len(solutions)}}
 
   return canonical(cert)==canonical(expected)
  except (ValueError,KeyError,TypeError,IndexError,AttributeError):return False

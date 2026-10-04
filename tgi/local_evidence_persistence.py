"""Closed-schema lossless DAG storage for complete owned native evidence."""
import math
from dataclasses import fields
from fractions import Fraction
from types import MappingProxyType
from tgi.spatial import Atom,SpatialBond,LatticeView
from tgi.frame_engine import Receipt
ENCODING='TGI-ORDERED-EVIDENCE-GRAPH-V2'
CLASSES={c.__name__:c for c in (Atom,SpatialBond,LatticeView,Receipt)}

def pack(value,budget):
 memo={};active=set()
 def walk(value):
  budget.consume()
  if value is None or type(value) in (str,int,bool):return value
  if type(value) is float and math.isfinite(value):return value
  kind=type(value);name=next((n for n,c in CLASSES.items() if kind is c),None)
  if kind not in (dict,list,tuple,MappingProxyType,Fraction) and name is None:raise TypeError('Unsupported original evidence type')
  key=id(value)
  if key in active:raise ValueError('Cyclic evidence cannot authorize an acyclic native source')
  if key in memo:return {'t':'ref','i':memo[key]}
  index=len(memo);memo[key]=index;active.add(key)
  if kind in (dict,MappingProxyType):tag='dict' if kind is dict else 'mappingproxy';items=[[walk(k),walk(v)] for k,v in value.items()]
  elif kind in (tuple,list):tag=kind.__name__;items=[walk(v) for v in value]
  elif kind is Fraction:tag='fraction';items=[walk(value.numerator),walk(value.denominator)]
  else:tag=name;items=[[field.name,walk(getattr(value,field.name))] for field in fields(value)]
  active.remove(key);return {'t':tag,'i':index,'v':items}
 return walk(value)

def unpack(value,budget):
 memo={};pending=object()
 def walk(value):
  budget.consume()
  if value is None or type(value) in (str,int,bool):return value
  if type(value) is float and math.isfinite(value):return value
  if type(value) is not dict or type(value.get('t')) is not str or type(value.get('i')) is not int:raise ValueError('Invalid typed graph node')
  tag,index=value['t'],value['i']
  if tag=='ref':
   if set(value)!={'t','i'} or index not in memo or memo[index] is pending:raise ValueError('Invalid or cyclic original reference')
   return memo[index]
  if set(value)!={'t','i','v'} or type(value['v']) is not list or index!=len(memo):raise ValueError('Original sequential graph node required')
  memo[index]=pending;rows=value['v']
  if tag in ('dict','mappingproxy'):
   result={}
   for row in rows:
    if type(row) is not list or len(row)!=2:raise ValueError('Invalid original mapping entry')
    key=walk(row[0])
    try:
     if key in result:raise ValueError('Duplicated original mapping key')
     result[key]=walk(row[1])
    except TypeError as error:raise ValueError('Invalid original mapping key') from error
   if tag=='mappingproxy':result=MappingProxyType(result)
  elif tag in ('list','tuple'):
   items=[walk(v) for v in rows];result=items if tag=='list' else tuple(items)
  elif tag=='fraction':
   if len(rows)!=2:raise ValueError('Exact fraction numerator/denominator required')
   numerator,denominator=[walk(v) for v in rows]
   if type(numerator) is not int or type(denominator) is not int or denominator<=0:raise ValueError('Invalid exact fraction')
   result=Fraction(numerator,denominator)
   if result.numerator!=numerator or result.denominator!=denominator:raise ValueError('Canonical original fraction required')
  elif tag in CLASSES:
   cls=CLASSES[tag];expected=[field.name for field in fields(cls)]
   if [row[0] for row in rows if type(row) is list and len(row)==2]!=expected or len(rows)!=len(expected):raise ValueError('Exact closed native field schema required')
   result=cls(**{row[0]:walk(row[1]) for row in rows})
  else:raise ValueError('Unknown native graph type')
  memo[index]=result;return result
 return walk(value)

"""Neutral matching/cover bounds; no semantic pairing selection."""
from tgi.role_work import RoleSearchBudget

def certify_capacity_graph(left,right,edges,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
        left=sorted(left);right=sorted(right);l=set(left);r=set(right)
        if len(left)!=len(l) or len(right)!=len(r):raise ValueError('Duplicate vertex')
        adjacent={a:set() for a in left}
        for pair in edges:
            budget.consume()
            if len(pair)!=2 or pair[0] not in l or pair[1] not in r:raise ValueError('Invalid edge')
            adjacent[pair[0]].add(pair[1])
        adjacent={a:sorted(bs) for a,bs in adjacent.items()};mate={};matched={}
        for root in left:
            budget.consume();stack=[(root,iter(adjacent[root]))];seen=set();parent={};free=None
            while stack and free is None:
                budget.consume();a,it=stack[-1]
                try:b=next(it)
                except StopIteration:stack.pop();continue
                if b in seen:continue
                seen.add(b);parent[b]=a
                if b not in mate:free=b;break
                child=mate[b];stack.append((child,iter(adjacent[child])))
            while free is not None:
                budget.consume();a=parent[free];previous=matched.get(a);matched[a]=free;mate[free]=a;free=previous
        zl=l-set(matched);zr=set();pending=list(zl)
        while pending:
            budget.consume();a=pending.pop()
            for b in adjacent[a]:
                budget.consume()
                if matched.get(a)==b or b in zr:continue
                zr.add(b)
                if b in mate and mate[b] not in zl:zl.add(mate[b]);pending.append(mate[b])
        return dict(capacity=len(mate),matching=[list(p) for p in sorted(matched.items())],cover_left=sorted(l-zl),cover_right=sorted(zr))


def verify_capacity_graph(left,right,edges,c,*,max_search_steps=None):
    budget=RoleSearchBudget(max_search_steps)
    with budget.scope():
      try:
        if not isinstance(c,dict) or set(c)!={'capacity','matching','cover_left','cover_right'} or type(c['capacity']) is not int:return False
        l=set(left);r=set(right)
        if len(l)!=len(left) or len(r)!=len(right):return False
        e=set()
        for pair in edges:
            budget.consume()
            if len(pair)!=2 or pair[0] not in l or pair[1] not in r:return False
            e.add(tuple(pair))
        seen_left=set();seen_right=set()
        for pair in c['matching']:
            budget.consume()
            if len(pair)!=2 or tuple(pair) not in e:return False
            a,b=pair
            if a in seen_left or b in seen_right:return False
            seen_left.add(a);seen_right.add(b)
        cover=[]
        for vertices,allowed in ((c['cover_left'],l),(c['cover_right'],r)):
            values=set()
            for v in vertices:
                budget.consume()
                if v not in allowed or v in values:return False
                values.add(v)
            cover.append(values)
        if len(c['matching'])!=c['capacity'] or c['capacity']!=sum(map(len,cover)):return False
        for a,b in e:
            budget.consume()
            if a not in cover[0] and b not in cover[1]:return False
        return True
      except (ValueError,TypeError,KeyError,IndexError):return False

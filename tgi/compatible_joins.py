"""Complete compatible subsets via monotone interval-conflict exclusion."""
from itertools import combinations


def compatible_subsets(axes,budget):
    valid=[];conflicts=[0]*len(axes)
    def overlaps(a,b):
        return a[0]==b[0] and max(a[1],b[1])<min(a[2],b[2])
    for i,axis in enumerate(axes):
        broken=False
        for a,b in combinations(axis,2):
            budget.consume()
            if overlaps(a,b):broken=True;break
        if not broken:valid.append(i)
    for i,j in combinations(valid,2):
        collision=False
        for a in axes[i]:
            for b in axes[j]:
                budget.consume()
                if overlaps(a,b):collision=True;break
            if collision:break
        if collision:conflicts[i]|=1<<j;conflicts[j]|=1<<i
    available=sum(1<<i for i in valid)
    stack=[((),available)]
    while stack:
        selected,remaining=stack.pop()
        while remaining:
            budget.consume()
            bit=remaining & -remaining;i=bit.bit_length()-1;remaining-=bit
            subset=selected+(i,)
            yield tuple(axes[k] for k in subset)
            following=remaining & ~conflicts[i]
            if following:stack.append((subset,following))

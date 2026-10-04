"""Inherited search accounting for composed relational verification."""
from .incremental import SearchBudget,FormationSearchLimit,ACTIVE_SEARCH_BUDGET


class RoleSearchBudget(SearchBudget):
    def __init__(self,limit=None):
        super().__init__(limit)
        self.parent=ACTIVE_SEARCH_BUDGET.get()

    def consume(self):
        if self.limit is not None and self.used>=self.limit:
            raise FormationSearchLimit(self.limit,self.used)
        if self.parent is not None:self.parent.consume()
        SearchBudget.consume(self)

    def consume_many(self,count):
        """Exactly repeat consume, batching only known neutral counter classes."""
        if type(count) is not int or count<0:
            raise ValueError('Work count must be a nonnegative integer')
        chain=[];node=self
        while node is not None:
            if type(node) not in (RoleSearchBudget,SearchBudget):
                for _ in range(count):self.consume()
                return
            chain.append(node)
            node=node.parent if type(node) is RoleSearchBudget else None
        available=count
        for node in chain:
            if node.limit is not None:available=min(available,max(0,node.limit-node.used))
        for node in chain:node.used+=available
        if available<count:self.consume()

    def match_step(self):
        if self.limit is not None and self.used>=self.limit:
            raise FormationSearchLimit(self.limit,self.used)
        if self.parent is not None:self.parent.match_step()
        SearchBudget.consume(self)
        self.matcher_used+=1


def check_role_response(model,role,history,certificate,*,max_search_steps=None):
    from .role_response_check import verify_role_response
    budget=RoleSearchBudget(max_search_steps)
    result={'status':'NOT_VERIFIED','verified':False,'search_steps':0,'matcher_steps':0,
            'max_search_steps':max_search_steps}
    try:
        with budget.scope():
            valid=verify_role_response(model,role,history,certificate)
            result.update(status='VERIFIED' if valid else 'NOT_VERIFIED',verified=valid)
    except FormationSearchLimit as error:
        result.update(status='WORK_LIMIT',verified=False,exhausted_limit=error.limit)
    finally:
        result.update(search_steps=budget.used,matcher_steps=budget.matcher_used)
    return result

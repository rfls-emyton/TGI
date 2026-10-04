"""Instrumented verification with complete-or-unverified matcher work."""
from .incremental import SearchBudget, FormationSearchLimit, ACTIVE_SEARCH_BUDGET
from .organization_check import verify_resolution, verify_refusal
from .organization_snapshot import snapshot


class _VerificationBudget(SearchBudget):
    def __init__(self,limit,parent):
        super().__init__(limit);self.parent=parent

    def match_step(self):
        # Preflight the child before charging any ancestor. Ancestors perform
        # the same preflight, so rejected work is charged nowhere in the chain.
        if self.limit is not None and self.used>=self.limit:
            raise FormationSearchLimit(self.limit,self.used)
        if self.parent is not None:self.parent.match_step()
        super().match_step()


def check_resolution(engine,prefix,result,*,terminal_only=False,max_match_steps=None):
    budget=_VerificationBudget(max_match_steps,ACTIVE_SEARCH_BUDGET.get())
    report={"status":"NOT_VERIFIED","verified":False,"match_steps":0,"max_match_steps":max_match_steps}
    try:
        with budget.scope():
            if engine._dirty:return report
            kind=result.get("status")
            if kind not in ("RESOLVED","NO_PATH","AMBIGUOUS"):return report
            frozen=snapshot(engine)
            checker=verify_resolution if kind=="RESOLVED" else verify_refusal
            verified=checker(frozen,prefix,result,terminal_only=terminal_only)
            report.update(status="VERIFIED" if verified else "NOT_VERIFIED",verified=verified)
    except FormationSearchLimit as error:
        report.update(status="WORK_LIMIT",verified=False,exhausted_limit=error.limit)
    except (KeyError,IndexError,TypeError,ValueError,AttributeError):
        report.update(status="NOT_VERIFIED",verified=False)
    finally:
        report["match_steps"]=budget.matcher_used
    return report


def check_ask_certificate(engine, certificate, *, max_match_steps=None):
    """Check complete search scope; exhausted work never proves absence."""
    from .ask_certificate import verify_ask_certificate
    budget = _VerificationBudget(max_match_steps, ACTIVE_SEARCH_BUDGET.get())
    report = {"status": "NOT_VERIFIED", "verified": False,
              "match_steps": 0, "max_match_steps": max_match_steps}
    try:
        with budget.scope():
            if engine._dirty:
                return report
            verified = verify_ask_certificate(engine, certificate)
            report.update(status="VERIFIED" if verified else "NOT_VERIFIED",
                          verified=verified)
    except FormationSearchLimit as error:
        report.update(status="WORK_LIMIT", verified=False,
                      exhausted_limit=error.limit)
    except (KeyError, IndexError, TypeError, ValueError, AttributeError):
        report.update(status="NOT_VERIFIED", verified=False)
    finally:
        report["match_steps"] = budget.matcher_used
    return report


class TemporalCandidateLimit(FormationSearchLimit):
    """Separate work unit: pool candidate or Cartesian tuple examination."""


class _TemporalCandidateBudget(SearchBudget):
    def __init__(self,limit,parent):
        super().__init__(limit);self.parent=parent

    def consume(self):
        if self.limit is not None and self.used>=self.limit:
            raise TemporalCandidateLimit(self.limit,self.used)
        if self.parent is not None:self.parent.consume()
        super().consume()


def check_recent_certificate(engine,certificate,*,max_match_steps=None,max_candidates=None):
    """Verify temporal completeness under independent matcher/candidate ceilings."""
    from .recent_observation import verify_recent_at,ACTIVE_TEMPORAL_CANDIDATES
    matches=_VerificationBudget(max_match_steps,ACTIVE_SEARCH_BUDGET.get())
    candidates=_TemporalCandidateBudget(max_candidates,ACTIVE_TEMPORAL_CANDIDATES.get())
    report={'status':'NOT_VERIFIED','verified':False,'match_steps':0,'candidate_steps':0,
            'max_match_steps':max_match_steps,'max_candidates':max_candidates}
    token=ACTIVE_TEMPORAL_CANDIDATES.set(candidates)
    try:
        with matches.scope():
            verified=verify_recent_at(engine,certificate)
            report.update(status='VERIFIED' if verified else 'NOT_VERIFIED',verified=verified)
    except TemporalCandidateLimit as error:
        report.update(status='WORK_LIMIT',verified=False,exhausted_kind='candidates',exhausted_limit=error.limit)
    except FormationSearchLimit as error:
        report.update(status='WORK_LIMIT',verified=False,exhausted_kind='matcher',exhausted_limit=error.limit)
    finally:
        ACTIVE_TEMPORAL_CANDIDATES.reset(token)
        report.update(match_steps=matches.matcher_used,candidate_steps=candidates.used)
    return report

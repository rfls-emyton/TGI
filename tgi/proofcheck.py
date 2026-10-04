"""Fact certificate checks that never invoke the answer producer."""
from .identity import decode
from .frame_engine import canonical


def _schema_valid(engine, source, schema):
    from .grounding import pattern_from_grounding
    entry = engine.demonstrations.get(source)
    if entry is None or entry[1] != schema or not engine.store.alive(source):
        return False
    raw, _, binding = entry
    return (engine.store.records[source][0] == raw
            and pattern_from_grounding(raw, dict(binding)) == schema.pattern)


def _assertion_valid(engine, assertion):
    if not engine.store.alive(assertion.source_id) or not assertion.demonstrations:
        return False
    raw = engine.store.records[assertion.source_id][0]
    spans = {role:(start,stop) for role,start,stop in assertion.spans}
    if set(spans) != {"subject","object"}:
        return False
    for role,(start,stop) in spans.items():
        if type(start) is not int or type(stop) is not int or not 0 <= start < stop <= len(raw):
            return False
        if raw[start:stop] != getattr(assertion,role):
            return False
    bindings = set()
    for source in assertion.demonstrations:
        entry = engine.demonstrations.get(source)
        if entry is None:
            return False
        schema = entry[1]
        if (schema.kind,schema.predicate,schema.polarity,schema.quantifier) != ("fact",assertion.predicate,assertion.polarity,assertion.quantifier):
            return False
        if not _schema_valid(engine,source,schema) or spans not in schema.pattern.matches(raw):
            return False
        bindings.add(entry[2])
    return len(bindings) >= 3


def verify_grounded(engine, raw, result, world="default"):
    try:
        return _verify(engine,raw,result,world)
    except (KeyError,TypeError,ValueError,AttributeError,IndexError):
        return False


def _verify(engine,raw,result,world):
    if not isinstance(result,dict) or result.get("status") != "RESOLVED":
        return False
    status, parsed = engine._parse(raw,"query")
    if status != "RESOLVED":
        return False
    schema, ports, query_support = parsed
    if not all(_schema_valid(engine,s,schema) for s in query_support):
        return False
    bound_role = next(iter(ports))
    start,stop = ports[bound_role]
    bound = raw[start:stop]
    output_role = "object" if bound_role == "subject" else "subject"
    possibilities = {}
    for assertion in engine.assertions.values():
        if assertion.world != world or assertion.predicate != schema.predicate:
            continue
        rows = []
        if assertion.quantifier == schema.quantifier and getattr(assertion,bound_role) == bound:
            rows.append((getattr(assertion,output_role),(),assertion))
        elif assertion.quantifier == "all" and schema.quantifier == "one":
            if bound_role == "subject":
                subjects = [bound]
            elif assertion.object == bound:
                subjects = sorted({a.subject for a in engine.assertions.values()
                                   if a.world == world and a.predicate == "is_a" and a.polarity == 1})
            else:
                subjects = []
            for subject in subjects:
                paths,broken,conflict = engine._memberships(subject,world)
                if broken or conflict:
                    return False
                path = paths.get(assertion.subject)
                if path:
                    for source in path:
                        if not _assertion_valid(engine,engine.assertions[source]):
                            return False
                    answer_source = assertion if bound_role == "subject" else engine.assertions[path[0]]
                    value = assertion.object if bound_role == "subject" else subject
                    rows.append((value,path,answer_source))
        if rows and not _assertion_valid(engine,assertion):
            return False
        for value,path,answer_source in rows:
            possibilities.setdefault(value,{}).setdefault(assertion.polarity,[]).append((assertion,path,answer_source))
    if any(1 in signs and -1 in signs for signs in possibilities.values()):
        return False
    expected = sorted(v for v,signs in possibilities.items() if schema.polarity in signs)
    if not expected or result.get("answers") != expected or len(result.get("proofs",[])) != len(expected):
        return False
    view = engine.store.frames.view()
    for value,proof in zip(expected,result["proofs"]):
        accepted = False
        for assertion,path,answer_source in possibilities[value][schema.polarity]:
            span = next((a,b) for role,a,b in answer_source.spans if role == output_role)
            _,anchor = engine.store.records[answer_source.source_id]
            origin = view.origins[anchor]
            coordinates = tuple((origin[0]+i,*origin[1:]) for i in range(*span))
            if decode(view.atoms[p].identity for p in coordinates) != value:
                continue
            expected_proof = {"answer":value,"source_id":answer_source.source_id,"span":span,
                              "relation_source_id":assertion.source_id,"coordinates":coordinates,
                              "membership_sources":path,"fact_demonstrations":assertion.demonstrations,
                              "query_demonstrations":query_support}
            if canonical(proof) == canonical(expected_proof):
                accepted = True
                break
        if not accepted:
            return False
    return True

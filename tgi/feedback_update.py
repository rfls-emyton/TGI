"""Prepare a separate model from certified actual feedback; never mutate inputs."""
from copy import deepcopy
from .identity import decode,encode
from .role_feedback_check import verify_role_feedback
from .role_projection import project_roles
from .role_eligibility import certify_role_eligibility
from .role_candidates import certify_role_candidates
from .observed_response import certify_observed_response


def prepare_feedback_update(model,role,acquisition,feedback,source,*,max_formation_steps=None):
    if not isinstance(source,str) or not source.strip():raise ValueError('New source required')
    encode(source)
    if source in model.episodes:raise ValueError('Source already exists')
    if not verify_role_feedback(model,role,acquisition,feedback):raise ValueError('Invalid feedback')
    proposal=feedback['proposal'];context=proposal['context']
    raw=acquisition.episodes[context['source']][0][context['start']:feedback['feedback']['response_frame']+1]
    updated=deepcopy(model)
    updated.observe(source,list(map(decode,raw)))
    updated.form(max_search_steps=max_formation_steps)
    updated_role=project_roles(updated,max_search_steps=max_formation_steps)
    eligibility=certify_role_eligibility(updated,updated_role)
    before=proposal['candidates']
    after=certify_role_candidates(updated,updated_role,eligibility,before['prefix'],before['query'])
    prefix=before['prefix']+[before['query']]
    certificate={'feedback':feedback,'source':source,'after_candidates':after,
                 'observed_before':certify_observed_response(model,prefix),
                 'observed_after':certify_observed_response(updated,prefix)}
    from .feedback_update_check import verify_feedback_update
    if not verify_feedback_update(model,role,acquisition,updated,updated_role,certificate):
        raise ValueError('Prepared feedback transition did not verify')
    return updated,updated_role,certificate

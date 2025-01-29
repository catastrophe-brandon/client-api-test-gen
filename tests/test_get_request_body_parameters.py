import json

from target_conversion import get_request_body_parameters


def test_get_request_body_parameters():

    full_spec = json.load(open("./tests/data/notif_v2_spec.json"))

    # path with a simple request body, single object as input
    parameters = get_request_body_parameters(
        full_spec, "/notifications/behaviorGroups", "post"
    )
    assert len(parameters) == 1

    # parameter is an array of items
    array_parameters = get_request_body_parameters(
        full_spec, "/notifications/behaviorGroups/{behaviorGroupId}/actions", "put"
    )
    assert len(array_parameters) == 1
    assert array_parameters[0].type == "array"
    assert array_parameters[0].aggregate_info is not None
    assert array_parameters[0].name == "requestBody"

    # parameter is a ref
    ref_parameter = get_request_body_parameters(
        full_spec, "/org-config/daily-digest/time-preference", "put"
    )
    assert len(ref_parameter) == 1
    assert ref_parameter[0].ref == "#/components/schemas/LocalTime"

    # no req body parameters
    no_params = get_request_body_parameters(
        full_spec, "/notifications/facets/bundles", "get"
    )
    assert len(no_params) == 0


def test_get_request_body_parameters_unnamed():
    """
    Get request body parameters for an endpoint that has "unnamed" parameters
    :return:
    """

    spec_path = "/notifications/behaviorGroups/{behaviorGroupId}/actions"
    spec_verb = "put"

    full_spec = json.load(open("./tests/data/notif_v2_spec.json"))
    req_body_params = get_request_body_parameters(full_spec, spec_path, spec_verb)
    assert len(req_body_params) == 1
    assert req_body_params[0].unique is False

    # Now the case where unique is True
    # TODO

import json

from target_conversion import (
    get_request_body_parameters,
    get_url_embedded_parameters,
    build_param_string,
    RequestBodyParameter,
    build_dependent_param_string,
)

full_spec = json.load(open("./tests/data/notif_v1_spec.json"))


def test_build_dependent_param_string():
    # single dependent parameter
    dependent_param = RequestBodyParameter(
        name=None,
        type=None,
        ref="#/components/schemas/UpdateBehaviorGroupRequest",
        aggregate_info=None,
    )

    dependent_param_str = build_dependent_param_string(full_spec, [dependent_param])
    assert (
        dependent_param_str
        == "const updateBehaviorGroupRequest : UpdateBehaviorGroupRequest = { };"
    )


def test_build_param_string():
    spec_path = "/notifications/behaviorGroups/{id}"
    spec_verb = "put"

    req_body_params = get_request_body_parameters(full_spec, spec_path, spec_verb)
    assert len(req_body_params) == 1

    url_embedded_params = get_url_embedded_parameters(full_spec, spec_path, spec_verb)
    assert len(url_embedded_params) == 1

    result = build_param_string(full_spec, req_body_params, url_embedded_params)
    assert len(result) == 2
    assert (
        result[0]
        == "const updateBehaviorGroupRequest : UpdateBehaviorGroupRequest = { };"
    )
    assert result[1].startswith("id:")
    assert result[1].endswith("updateBehaviorGroupRequest")

import json

from target_conversion import (
    get_request_body_parameters,
    get_url_embedded_parameters,
    build_param_string,
    build_dependent_param_string,
)

from target_conversion.data_modeling import RequestBodyParameter

full_spec = json.load(open("./tests/data/notif_v2_spec.json"))


def test_build_dependent_param_string():
    # single dependent parameter
    dependent_param = RequestBodyParameter(
        name=None,
        type=None,
        ref="#/components/schemas/UpdateBehaviorGroupRequest",
        unique=False,
        aggregate_info=None,
        example=None,
    )

    dependent_param_str = build_dependent_param_string(full_spec, [dependent_param])
    assert (
        dependent_param_str
        == "const updateBehaviorGroupRequest : UpdateBehaviorGroupRequest = {  };"
    )


def test_build_param_string():
    """
    When both the embedded params and the request body params are included, both should
    be found in the response from the function call
    """
    spec_path = "/notifications/behaviorGroups/{id}"
    spec_verb = "put"

    req_body_params = get_request_body_parameters(full_spec, spec_path, spec_verb)
    assert len(req_body_params) == 1

    url_embedded_params = get_url_embedded_parameters(full_spec, spec_path, spec_verb)
    assert len(url_embedded_params) == 1

    result = build_param_string(full_spec, req_body_params, url_embedded_params)
    # Confirm the request object was instantiated
    assert len(result) == 3
    assert (
        result[0]
        == "const updateBehaviorGroupRequest : UpdateBehaviorGroupRequest = {  };"
    )
    # Confirm the API client call param list was generated
    assert result[1].startswith("id:")
    assert result[1].endswith("updateBehaviorGroupRequest")


def test_build_param_string_with_embedded_params_only():
    """When we remove the request body params, they should not appear in the generated string"""
    spec_path = "/notifications/behaviorGroups/{id}"
    spec_verb = "put"
    result = build_param_string(
        full_spec,
        None,
        url_parameters=get_url_embedded_parameters(full_spec, spec_path, spec_verb),
    )
    assert result[0] is ""


def test_build_param_string_with_request_body_params_only():
    """When we remove the embedded URL params, they should not appear in the generated string"""
    spec_path = "/notifications/behaviorGroups/{id}"
    spec_verb = "put"
    result = build_param_string(
        full_spec,
        req_body_parameters=get_request_body_parameters(
            full_spec, spec_path, spec_verb
        ),
        url_parameters=None,
    )
    assert "id:" not in result[1]


def test_build_param_string_create_behavior_group():
    """Confirm it works with a different endpoint"""
    spec_path = "/notifications/behaviorGroups"
    spec_verb = "post"
    result = build_param_string(
        full_spec,
        req_body_parameters=get_request_body_parameters(
            full_spec, spec_path, spec_verb
        ),
        url_parameters=None,
    )
    assert (
        result[0]
        == 'const createBehaviorGroupRequest : CreateBehaviorGroupRequest = { display_name: "" };'
    )
    assert result[1] == "createBehaviorGroupRequest"


def test_build_param_string_with_unnamed_param():
    """When spec parameters to not have an explicit name, the value returned should include 'requestBody'"""

    # Example endpoint is "update behavior group actions"
    spec_path = "/notifications/behaviorGroups/{behaviorGroupId}/actions"
    spec_verb = "put"

    result = build_param_string(
        full_spec,
        req_body_parameters=get_request_body_parameters(
            full_spec, spec_path, spec_verb
        ),
        url_parameters=None,
    )

    assert "requestBody: []" in result[1]


def test_build_param_string_with_local_time():

    spec_path = "/org-config/daily-digest/time-preference"
    spec_verb = "put"

    result = build_param_string(
        full_spec,
        req_body_parameters=get_request_body_parameters(
            full_spec, spec_path, spec_verb
        ),
        url_parameters=None,
        include_all=True,
    )
    assert result[0] == ""
    assert result[1] == 'localTime: "13:45:30.123456789"'

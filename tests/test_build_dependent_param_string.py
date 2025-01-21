import json

from target_conversion import (
    build_dependent_param_string,
    RequestBodyParameter,
)


def test_build_dependent_param_string():
    """Build the param string for a dependent parameter and verify the output is correct"""
    full_spec = json.load(open("./tests/data/notif_v2_spec.json"))
    ref = "#/components/schemas/CreateBehaviorGroupRequest"
    dependent_params = [RequestBodyParameter(None, None, ref, None)]
    dependant_params_str = build_dependent_param_string(full_spec, dependent_params)
    assert (
        dependant_params_str
        == 'const createBehaviorGroupRequest : CreateBehaviorGroupRequest = { displayName: "" };'
    )


def test_build_dependent_param_string_local_time():
    """When the dependent param is local time, verify the output is correct"""
    full_spec = json.load(open("./tests/data/notif_v2_spec.json"))
    ref = "#/components/schemas/LocalTime"
    dependent_params = [RequestBodyParameter(None, None, ref, None)]
    dependent_params_str = build_dependent_param_string(
        full_spec, dependent_params, include_all=True
    )
    assert dependent_params_str == 'const localTime : LocalTime = { "" };'

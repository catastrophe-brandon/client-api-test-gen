import json

from target_conversion import (
    build_dependent_param_string,
    RequestBodyParameter,
)

full_spec = json.load(open("./tests/data/notif_v2_spec.json"))


def test_build_dependent_param_string():
    """Build the param string for a dependent parameter and verify the output is correct"""
    ref = "#/components/schemas/CreateBehaviorGroupRequest"
    dependent_params = [RequestBodyParameter(None, None, ref, None, None)]
    dependant_params_str = build_dependent_param_string(full_spec, dependent_params)
    assert (
        dependant_params_str
        == 'const createBehaviorGroupRequest : CreateBehaviorGroupRequest = { display_name: "" };'
    )


def test_build_dependent_param_string_local_time():
    """When the dependent param is local time, verify the output is correct"""
    ref = "#/components/schemas/LocalTime"
    dependent_params = [RequestBodyParameter(None, None, ref, None, None)]
    dependent_params_str = build_dependent_param_string(
        full_spec, dependent_params, include_all=True
    )
    assert dependent_params_str == 'const localTime : LocalTime = { "" };'


"""
const createBehaviorGroupRequest : CreateBehaviorGroupRequest = { bundleId: None, bundleName: "", displayName: "", endpointIds: [], eventTypeIds: [], bundleUuidOrBundleNameValid: true };
"""


def test_build_dependant_param_string_multiple_dependent_params():
    """
    When dependent parameters have their own dependencies, we need to also build those parameters
    Primary example: bundleId has a ref to the UUID schema
    :return:
    """

    ref = "#/components/schemas/CreateBehaviorGroupRequest"
    dependent_params = [
        RequestBodyParameter(
            name=None, type=None, ref=ref, unique=False, aggregate_info=None
        )
    ]
    dependant_params_str = build_dependent_param_string(
        full_spec, dependent_params, include_all=True
    )
    assert 'bundleId: "' in dependant_params_str

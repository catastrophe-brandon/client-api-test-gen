import json

from target_conversion import (
    build_dependent_param_string,
    RequestBodyParameter,
)

full_spec = json.load(open("./tests/data/notif_v2_spec.json"))


def test_build_dependent_param_string():
    """Build the param string for a dependent parameter and verify the output is correct"""
    ref = "#/components/schemas/CreateBehaviorGroupRequest"
    dependent_params = [RequestBodyParameter(None, None, ref, None, None, None)]
    dependant_params_str = build_dependent_param_string(full_spec, dependent_params)
    assert (
        dependant_params_str
        == 'const createBehaviorGroupRequest : CreateBehaviorGroupRequest = { display_name: "" };'
    )

    dependant_params_str = build_dependent_param_string(
        full_spec, dependent_params, include_all=True
    )
    assert 'bundle_id: "' in dependant_params_str
    assert 'bundle_name: ""' in dependant_params_str
    assert 'display_name: ""' in dependant_params_str
    assert "endpoint_ids: []" in dependant_params_str
    assert "event_type_ids: new Set<string>()" in dependant_params_str
    assert "bundle_uuid_or_bundle_name_valid: true" in dependant_params_str


def test_build_dependent_params_for_update_behavior_group():
    """UpdateBehaviorGroupRequest has a longer set of parameters good for testing"""
    ref = "#/components/schemas/UpdateBehaviorGroupRequest"
    dependent_params = [RequestBodyParameter(None, None, ref, None, None, None)]
    dependant_params_str = build_dependent_param_string(
        full_spec, dependent_params, include_all=True
    )
    assert (
        'display_name: "", endpoint_ids: [], event_type_ids: new Set<string>(), display_name_not_null_and_blank: true'
        in dependant_params_str
    )


# def test_build_dependent_param_string_local_time():
#     """When the dependent param is local time, verify the output is correct"""
#     ref = "#/components/schemas/LocalTime"
#     dependent_params = [RequestBodyParameter(None, None, ref, None, None, None)]
#     dependent_params_str = build_dependent_param_string(
#         full_spec, dependent_params, include_all=True
#     )
#     # Confirm it uses the example value from the spec
#     assert (
#         dependent_params_str
#         == 'const localTime : string = "13:45:30.123456789";'
#     )


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
            name=None,
            type=None,
            ref=ref,
            unique=False,
            aggregate_info=None,
            example=None,
        )
    ]
    dependant_params_str = build_dependent_param_string(
        full_spec, dependent_params, include_all=True
    )
    assert 'bundle_id: "' in dependant_params_str

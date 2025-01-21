import json
from target_conversion import (
    build_dependent_param_string,
    RequestBodyParameter,
)


def test_build_dependent_param_string():
    """Build the param string for a dependent parameter and verify the output is correct"""
    full_spec = json.load(open("./tests/data/notif_v1_spec.json"))
    ref = "#/components/schemas/CreateBehaviorGroupRequest"
    dependent_params = [RequestBodyParameter(None, None, ref, None)]
    dependant_params_str = build_dependent_param_string(full_spec, dependent_params)
    assert (
        dependant_params_str
        == 'const createBehaviorGroupRequest : CreateBehaviorGroupRequest = { displayName: "" };'
    )

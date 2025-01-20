import json

from target_conversion import build_test_target

full_spec = json.load(open("./tests/data/notif_v1_spec.json"))


def test_build_test_target_embedded_params_only():
    """Build a test target with no embedded URL params and only a request body object"""
    spec_path = "/notifications/behaviorGroups/affectedByRemovalOfEndpoint/{endpointId}"
    spec_verb = "get"

    target = build_test_target(full_spec, spec_path, spec_verb)
    # parameter values is the string substituted directly into the api client function call
    assert "endpointId:" in target.parameter_api_client_call


def test_build_test_target_request_body_only():
    """Build a test target with no request body and only URL embedded params"""
    pass


def test_build_test_target_both_embedded_and_request_body():
    """Build a test target with both types of parameters"""
    pass


def test_build_test_target_neither():
    """Build a test target that has no parameters"""
    pass

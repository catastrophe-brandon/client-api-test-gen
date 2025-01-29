import json

from target_conversion import build_test_target

full_spec = json.load(open("./tests/data/notif_v2_spec.json"))


def test_build_test_target_embedded_params_only():
    """Build a test target with no embedded URL params and only a request body object"""
    spec_path = "/notifications/behaviorGroups/affectedByRemovalOfEndpoint/{endpointId}"
    spec_verb = "get"

    target = build_test_target(full_spec, spec_path, spec_verb)
    # parameter values is the string substituted directly into the api client function call
    assert "endpointId:" in target.parameter_api_client_call


def test_build_test_target_request_body_only():
    """Build a test target with no request body and only URL embedded params"""
    spec_path = "/org-config/daily-digest/time-preference"
    spec_verb = "put"

    target = build_test_target(full_spec, spec_path, spec_verb)
    # When a dependent parameter is a basic type, we collapse the parameter into the client call instead
    # of creating a dependent parameter
    assert target.parameter_dependent_objects == ""
    assert '"13:45:30.123456789"' in target.parameter_api_client_call


def test_build_test_target_both_embedded_and_request_body():
    """Build a test target with both types of parameters"""
    spec_path = "/notifications/eventTypes/{eventTypeId}/endpoints"
    spec_verb = "put"
    target = build_test_target(full_spec, spec_path, spec_verb)

    assert "" in target.parameter_dependent_objects
    assert "eventTypeId:" in target.parameter_api_client_call
    # Default value for an array type without a named parameter is empty array
    assert "new Set<string>()" in target.parameter_api_client_call

    # Check the expected response code
    assert target.expected_response == "200"


def test_build_test_target_neither():
    """Build a test target that has no parameters"""

    # Has no required parameters
    spec_path = "/notifications/eventTypes"
    spec_verb = "get"

    target = build_test_target(full_spec, spec_path, spec_verb)
    assert "" == target.parameter_dependent_objects
    assert "" == target.parameter_api_client_call

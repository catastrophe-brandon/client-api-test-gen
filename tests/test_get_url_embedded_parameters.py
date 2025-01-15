import json

from main import get_url_embedded_parameters


def test_get_url_embedded_parameters():
    """Gets the list of any url-embedded parameters from the spec"""

    # Try a url with embedded parameters first
    full_spec = json.load(open("./tests/data/notif_v1_spec.json"))
    spec_path = "/notifications/behaviorGroups/affectedByRemovalOfEndpoint/{endpointId}"
    spec_verb = "get"
    endpoint_params = get_url_embedded_parameters(full_spec, spec_path, spec_verb)
    assert len(endpoint_params) == 1
    assert endpoint_params[0].name == "endpointId"

    # Multiple embedded parameters
    endpoint_params_multi = get_url_embedded_parameters(
        full_spec,
        "/notifications/bundles/{bundleName}/applications/{applicationName}/eventTypes/{eventTypeName}",
        "get",
    )
    assert len(endpoint_params_multi) == 3

    # Try a url with no embedded parameters
    endpoint_params_empty = get_url_embedded_parameters(
        full_spec, "/notifications/behaviorGroups", "post"
    )
    assert len(endpoint_params_empty) == 0

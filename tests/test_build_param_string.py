import json

from target_conversion import (
    get_request_body_parameters,
    get_url_embedded_parameters,
    build_param_string,
)


def test_build_dependent_param_string():
    # build_dependent_params()
    pass


def test_build_param_string():
    spec_path = "/notifications/behaviorGroups/{id}"
    spec_verb = "put"
    full_spec = json.load(open("./tests/data/notif_v1_spec.json"))

    req_body_params = get_request_body_parameters(full_spec, spec_path, spec_verb)
    assert len(req_body_params) == 1

    url_embedded_params = get_url_embedded_parameters(full_spec, spec_path, spec_verb)
    assert len(url_embedded_params) == 1

    result = build_param_string(req_body_params, url_embedded_params)
    assert result != ""
    assert result[0] == ""
    assert result[1].startswith("id:")
    assert result[1].endswith("updateBehaviorGroupRequest")

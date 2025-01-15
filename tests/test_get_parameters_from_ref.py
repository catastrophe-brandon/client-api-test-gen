import json

from main import get_request_body_parameters_from_ref


def test_get_parameters_from_ref():
    full_spec = json.load(open("./tests/data/notif_v1_spec.json"))

    params = get_request_body_parameters_from_ref(
        full_spec, ref="#/components/schemas/CreateBehaviorGroupRequest"
    )
    assert len(params) == 1
    assert params[0].name == "display_name"
    assert params[0].type == "string"

    params = get_request_body_parameters_from_ref(
        full_spec, ref="#/components/schemas/UpdateBehaviorGroupRequest"
    )
    assert len(params) == 4
    assert params[0].name == "display_name"
    assert params[0].type == "string"
    assert params[1].name == "endpoint_ids"
    assert params[1].type == "array"
    assert params[1].ref is None
    assert params[1].aggregate_info == {
        "type": "string",
        "format": "uuid",
        "pattern": "[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}",
    }
    assert params[3].name == "display_name_not_null_and_blank"
    assert params[3].type == "boolean"


def test_get_parameters_from_ref_including_dependent_objects():
    """When a ref contains dependent objects, those objects need to be built as well."""

import json

from target_conversion import (
    RequestBodyParameter,
    render_params_as_string,
)

full_spec = json.load(open("./tests/data/notif_v2_spec.json"))


def test_render_param_values():
    """Verify that a series of 'flat' parameters are converted to a string properly"""
    endpt_jeff = RequestBodyParameter("jeff", "string", None, None, None, None)

    result = render_params_as_string(full_spec, [endpt_jeff])
    assert result == 'jeff: ""'


def test_render_param_values_for_update_behavior_group():

    # Body parameters taken from UpdateBehaviorGroup
    body_parameters = [
        RequestBodyParameter(
            name="display_name",
            type="string",
            ref=None,
            unique=False,
            aggregate_info=None,
            example=None,
        ),
        RequestBodyParameter(
            name="endpoint_ids",
            type="array",
            ref=None,
            unique=False,
            aggregate_info={
                "type": "string",
                "format": "uuid",
                "pattern": "[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}",
            },
            example=None,
        ),
        RequestBodyParameter(
            name="event_type_ids",
            type="array",
            ref=None,
            unique=True,
            aggregate_info={
                "type": "string",
                "format": "uuid",
                "pattern": "[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}",
            },
            example=None,
        ),
        RequestBodyParameter(
            name="display_name_not_null_and_blank",
            type="boolean",
            ref=None,
            unique=False,
            aggregate_info=None,
            example=None,
        ),
    ]
    result = render_params_as_string(full_spec, body_parameters)
    assert (
        result
        == 'display_name: "", endpoint_ids: [], event_type_ids: new Set<string>(), display_name_not_null_and_blank: true'
    )

import json

from target_conversion import (
    RequestBodyParameter,
    render_params_as_string,
)

full_spec = json.load(open("./tests/data/notif_v2_spec.json"))


def test_render_param_values():
    """Verify that a series of 'flat' parameters are converted to a string properly"""
    endpt_jeff = RequestBodyParameter("jeff", "string", None, None)

    result = render_params_as_string(full_spec, [endpt_jeff])
    assert result == 'jeff: ""'

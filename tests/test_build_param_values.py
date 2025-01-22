import json

import pytest

from target_conversion import (
    RequestBodyParameter,
    render_params_as_string,
    InvalidInputDataError,
)

full_spec = json.load(open("./tests/data/notif_v2_spec.json"))


def test_build_param_values():
    endpt_jeff = RequestBodyParameter("jeff", "string", None, None)

    result = render_params_as_string(full_spec, [endpt_jeff])
    assert result == 'jeff: ""'

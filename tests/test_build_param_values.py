from target_conversion import RequestBodyParameter, render_params_as_string


def test_build_param_values():
    endpt_jeff = RequestBodyParameter("jeff", "string", None, None)

    result = render_params_as_string([endpt_jeff])
    assert result == 'jeff: ""'

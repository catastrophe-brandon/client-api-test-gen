from target_conversion import RequestBodyParameter, build_param_values


def test_build_param_values():
    endpt_jeff = RequestBodyParameter("jeff", "string", None, None)

    result = build_param_values([endpt_jeff])
    assert result == 'Jeff: ""'

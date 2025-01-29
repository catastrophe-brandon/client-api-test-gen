from target_conversion import RequestBodyParameter, request_body_parameter_as_string


def test_req_body_param_as_string():

    input = RequestBodyParameter(
        name="requestBody",
        type="array",
        ref=None,
        unique=False,
        aggregate_info={
            "type": "string",
            "format": "uuid",
            "pattern": "[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}",
        },
        example=None,
    )

    result = request_body_parameter_as_string(input)
    assert result == "requestBody: []"


def test_req_body_parameter_as_string_with_local_time():
    input = RequestBodyParameter(
        name=None,
        type=None,
        ref="#/components/schemas/LocalTime",
        unique=False,
        aggregate_info=None,
        example="13:45:30.123456789",
    )
    # Direct call with a ref should not give any output. Maybe make this an error?
    result = request_body_parameter_as_string(input)
    assert result is None

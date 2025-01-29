from dataclasses import dataclass


@dataclass
class RequestBodyParameter(object):
    """
    Information about parameters used in a request body.
    """

    name: str | None
    type: str | None
    ref: str | None
    unique: bool | None
    aggregate_info: dict | None
    example: str | None


@dataclass
class ApiClientTarget(object):
    """
    Represents an individual endpoint to be tested based on info taken from the spec;
    bundles data for substitution into the final Mustache template
    """

    url_path: str
    verb: str
    summary: str
    operation_id: str
    request_class: str
    request_schema: str
    request_schema_class: str
    response_schema: str
    response_schema_class: str
    parameter_schema: str
    # The name of the class for the parameter, e.g. CreateBehaviorGroupRequest
    parameter_class: str
    parameter_api_client_call: str
    parameter_dependent_objects: str
    expected_response: str
    resolved_params: list[str]

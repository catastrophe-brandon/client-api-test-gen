"""
Code for converting information from the openapi spec into target format for template substitution.
"""

from dataclasses import dataclass


@dataclass
class RequestBodyParameter(object):
    """
    Information about parameters used in a request body.
    """

    name: str | None
    type: str | None
    ref: str | None
    aggregate_info: dict | None


def get_request_body_parameters_from_ref(
    full_spec: dict, ref: str
) -> list[RequestBodyParameter]:
    """
    Returns a list of required parameters for use with this endpoint based on info from the provided $ref

    If the endpoint specifies a ref as a parameter, this typically means that an additional "request" object needs to
    be created in the JS code.

    Note: Only returns parameters that are required at the moment.
    """
    split_ref = ref.split("/")
    split_ref.remove("#")
    cur = full_spec
    for tier in split_ref:
        cur = cur.get(tier)

    has_required = cur.get("required", False)

    if has_required:
        # only required parameters
        optional_or_required_params = cur["required"]
    else:
        # all parameters
        optional_or_required_params = list(cur["properties"].keys())

    return [
        copy_parameter_data(some_param, cur["properties"][some_param])
        for some_param in optional_or_required_params
    ]


@dataclass
class TestTarget(object):
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
    parameter_values: str


def build_test_target(full_spec: dict, path_value: str, verb_value: str) -> TestTarget:
    """
    Builds a TestTarget based on the information about an endpoint found in the spec
    :param full_spec: dict with all the openapi spec info
    :param path_value: endpoint path
    :param verb_value: http verb
    :return:
    """
    lookup_base = full_spec["paths"][path_value][verb_value]
    try:
        # If the request has a request body, gather the name as CamelCase for use later
        request_schema = lookup_base["requestBody"]["content"]["application/json"][
            "schema"
        ]["$ref"]
        parameter_schema = lookup_base["requestBody"]["content"]["application/json"][
            "schema"
        ]["$ref"]
        request_schema_class = request_schema.split("/")[-1]
    except KeyError:
        request_schema = ""
        request_schema_class = ""
        parameter_schema = ""

    try:
        # If the request has a response body schema, gather that info
        response_schema = lookup_base["responses"]["200"]["content"][
            "application/json"
        ]["schema"]["$ref"]
        response_schema_class = response_schema.split("/")[-1]
    except KeyError:
        response_schema = ""
        response_schema_class = ""

    if parameter_schema != "":
        try:
            # if there's a request body ref, determine the parameters from the schema ref
            parameters = get_request_body_parameters_from_ref(
                full_spec, parameter_schema
            )
        except Exception:
            parameters = []
    else:
        parameters = []

    request_class = convert_operation_id_to_classname(lookup_base["operationId"])
    param_values = build_param_values(parameters)

    test_target = TestTarget(
        url_path=path_value,
        verb=verb_value,
        summary=lookup_base["summary"],
        operation_id=lookup_base["operationId"],
        request_class=request_class,
        request_schema=request_schema,
        request_schema_class=request_schema_class,
        response_schema=response_schema,
        response_schema_class=response_schema_class,
        parameter_schema=parameter_schema,
        parameter_values=param_values,
    )
    return test_target


def get_request_body_parameters(
    full_spec: dict, spec_path: str, spec_verb: str
) -> list[RequestBodyParameter]:
    """Gets the list of request body parameters from the spec"""
    has_req_body = (
        full_spec["paths"][spec_path][spec_verb].get("requestBody", None) is not None
    )
    if not has_req_body:
        return []

    req_body_schema = full_spec["paths"][spec_path][spec_verb]["requestBody"][
        "content"
    ]["application/json"]["schema"]
    # schema is typically either a $ref or a single item with a type declaration and other info
    is_ref = req_body_schema.get("$ref", None) is not None
    result = []
    if is_ref:
        # do $ref things
        result.append(
            RequestBodyParameter(None, None, req_body_schema.get("$ref", None), None)
        )
    else:
        # param is a basic type
        item_type = req_body_schema.get("type", None)
        item_name = req_body_schema.get("name", None)
        item_items = req_body_schema.get("items", None)
        result.append(RequestBodyParameter(item_name, item_type, None, item_items))

    return result


@dataclass
class URLEmbeddedParameter(object):
    """
    Information about a param embedded in the url path
    """

    name: str
    schema: str | None
    type: str | None
    required: bool


def get_url_embedded_parameters(
    full_spec: dict, spec_path: str, spec_verb: str
) -> list[URLEmbeddedParameter]:
    """Gets the list of any url-embedded parameters from the spec"""
    result = []

    parameters = full_spec["paths"][spec_path][spec_verb].get("parameters", None)
    if parameters is None:
        return result

    for param in parameters:
        if param.get("in", None) == "path":
            result.append(
                URLEmbeddedParameter(
                    param.get("name"),
                    param.get("schema", None),
                    param.get("type", None),
                    param.get("required"),
                )
            )
    return result


def build_imports(
    import_class_prefix: str, test_target_data: list[TestTarget]
) -> list[str]:
    """Builds the data to populate the JS imports"""
    # Response classes
    import_names = [
        f"{import_class_prefix}{x.response_schema_class}"
        for x in test_target_data
        if x.response_schema_class != ""
    ]
    # Request classes
    import_names.extend(
        [
            f"{import_class_prefix}{y.request_schema_class}"
            for y in test_target_data
            if y.request_schema_class != ""
        ]
    )
    # Param classes
    import_names.extend(
        [
            f"{import_class_prefix}{z.request_schema_class}Params"
            for z in test_target_data
            if z.request_schema_class != ""
        ]
    )
    return import_names


def build_param_string(
    req_body_parameters: list[RequestBodyParameter],
    url_parameters: list[URLEmbeddedParameter],
) -> str:
    """
    Take the parameter info from the spec and convert it into a string of code that can be directly substituted into the
    template at the appropriate point.
    :param req_body_parameters:
    :param url_parameters:
    :return:
    """
    return ""


def build_param_values(parameters: list[RequestBodyParameter]) -> str:
    """Takes a list of EndpointParameter objects and converts it to a parameter string that can be
    substituted into the template for the specific test target."""
    result = []
    for endpt_param in parameters:
        name = camel_case(endpt_param.name)
        if endpt_param.type == "array":
            result.append(f"{name}: [],\n")
        elif endpt_param.type == "boolean":
            result.append(f"{name}: true,\n")
        elif endpt_param.type == "string":
            result.append(f'{name}: "",\n')
        elif endpt_param.type == "number":
            result.append(f"{name}: 0,\n")
        elif endpt_param.type == "object":
            result.append(f"{name}: null\n")
    return "".join(result)


def copy_parameter_data(name: str, parameter_data: dict) -> RequestBodyParameter:
    """Takes request body parameter from the spec and copies it into a RequestBodyParameter object"""
    type = parameter_data["type"]
    ref = parameter_data.get("ref", None)
    aggregate_info = parameter_data.get("items", None) if type == "array" else None
    return RequestBodyParameter(name, type, ref, aggregate_info)


def convert_operation_id_to_classname(name_from_json):
    """
    Removes any _ or $ and capitalizes name appropriately; for use in reformatting operationId
    to use in JS import statements
    """
    underscore_idx = name_from_json.index("_")
    temp_str = list(name_from_json)
    temp_str[underscore_idx + 1] = temp_str[underscore_idx + 1].upper()
    return "".join(temp_str).replace("_", "").replace("$", "")


def camel_case(name: str):
    """Takes a string_like_this and convert to StringLikeThis"""
    result = ""
    chunks = name.split("_")
    for chunk in chunks:
        result += chunk[0].upper() + chunk[1 : len(chunk)]
    return result

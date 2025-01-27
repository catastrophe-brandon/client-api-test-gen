"""
Code for converting information from the openapi spec into target format for template substitution.
"""

import uuid
from dataclasses import dataclass


class Spec(object):
    """Spec data loaded from an OpenAPI JSON spec file"""

    spec_data: dict

    def __init__(self, spec_data):
        self.spec_data = spec_data

    def get_ref(self, ref: str) -> dict:
        """
        Get the object associated with the ref value from the spec's data.
        :param ref:
        :return:
        """
        split_ref = ref.split("/")
        split_ref.remove("#")
        cur = self.spec_data
        for tier in split_ref:
            cur = cur.get(tier)
        return cur


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


def get_base_object_from_ref(ref: str) -> str:
    """Given a $ref returns the name of the object at the end of the ref as a string"""
    split_ref = ref.split("/")
    return split_ref[-1]


def get_ref_from_spec(full_spec: dict, ref: str) -> dict:
    """Given the spec info as a dict, get the definition object of the provided $ref"""
    split_ref = ref.split("/")
    split_ref.remove("#")
    cur = full_spec
    for tier in split_ref:
        cur = cur.get(tier)
    return cur


def get_request_body_parameters_from_ref(
    full_spec: dict, ref: str, include_optional=False
) -> list[RequestBodyParameter]:
    """
    Returns a list of required parameters for use with this endpoint based on info from the provided $ref

    If the endpoint specifies a ref as a parameter, this typically means that an additional "request" object needs to
    be created in the JS code.

    Note: Only returns parameters that are required at the moment.
    """

    cur = get_ref_from_spec(full_spec, ref)

    has_required = cur.get("required", False)

    if include_optional:
        # endpoint spec specified that the entire request body is required,
        # or we want to include all parameters for completeness
        if cur["type"] == "object":
            optional_or_required_params = list(cur["properties"].keys())
        else:
            # non-object data like a string
            return [RequestBodyParameter(None, cur["type"], None, None, None)]

    elif has_required:
        # only required parameters
        optional_or_required_params = cur["required"]
    else:
        # all parameters are optional; none required!
        return []

    return [
        copy_parameter_data(some_param, cur["properties"][some_param])
        for some_param in optional_or_required_params
    ]


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


def build_test_target(
    full_spec: dict, path_value: str, verb_value: str
) -> ApiClientTarget:
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

    request_class = convert_operation_id_to_classname(lookup_base["operationId"])
    req_body_parameters = get_request_body_parameters(full_spec, path_value, verb_value)
    url_parameters = get_url_embedded_parameters(full_spec, path_value, verb_value)

    # determine if all param values from a request body are required on the request
    try:
        include_all = lookup_base["requestBody"]["required"]
    except KeyError:
        include_all = False

    dependent_param_str, api_client_param_str = build_param_string(
        full_spec, req_body_parameters, url_parameters, include_all=include_all
    )

    # Each "Request" object has a "Params" object
    parameter_class = (
        (get_base_object_from_ref(parameter_schema).removesuffix("Request") + "Params")
        if parameter_schema != ""
        else ""
    )

    test_target = ApiClientTarget(
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
        parameter_class=parameter_class,
        parameter_api_client_call=api_client_param_str,
        parameter_dependent_objects=dependent_param_str,
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
            RequestBodyParameter(
                None, None, req_body_schema.get("$ref", None), None, None
            )
        )
    else:
        # param is a basic type
        item_type = req_body_schema.get("type", None)
        item_unique = req_body_schema.get("uniqueItems", False)
        item_name = req_body_schema.get("name", None)
        item_items = req_body_schema.get("items", None)
        # if no name was provided, we default to 'requestBody'
        if item_name is None:
            item_name = "requestBody"
        result.append(
            RequestBodyParameter(
                name=item_name,
                type=item_type,
                aggregate_info=item_items,
                unique=item_unique,
                ref=None,
            )
        )

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
            try:
                schema_type = param.get("schema").get("type")
            except KeyError:
                schema_type = None

            embedded_param = URLEmbeddedParameter(
                param.get("name"),
                param.get("schema", None),
                schema_type if schema_type is not None else param.get("type", None),
                param.get("required"),
            )
            result.append(embedded_param)
    return result


def build_param_imports(
    client_name, api_version, test_targets: list[ApiClientTarget]
) -> list[dict]:
    """Build the import data needed for the Param object imports"""
    import_data = []
    for test_target in test_targets:
        # e.g. "NotificationResourceV2CreateBehaviorGroupParams"
        friendly_operation_id = camel_case(test_target.operation_id.replace("$", ""))
        import_class = f"{friendly_operation_id}Params"
        import_package = f"{friendly_operation_id}"
        import_data.append(
            {"importClass": import_class, "importPackage": import_package}
        )
    return import_data


def build_request_imports(
    client_name, api_version, test_targets: list[ApiClientTarget]
) -> list[dict]:
    """
    Build the import data needed for the Request object imports
    :return:
    """
    import_data = []

    for test_target in test_targets:
        if test_target.parameter_class != "":
            import_class = f"{test_target.parameter_class}".replace("Params", "Request")
            import_package = "types"
            import_data.append(
                {"importClass": import_class, "importPackage": import_package}
            )
    return import_data


def build_imports(
    client_name,
    api_version,
    import_class_prefix: str,
    test_target_data: list[ApiClientTarget],
) -> list[dict]:
    """
    Builds the data to populate the JS imports based on data extracted from the spec
    :returns: a list of string pairs with the name of the class and the name of the source package
    """
    # Client class
    imports = [{"importClass": f"{client_name}Client", "importPackage": "api"}]
    folder_name_prefix = client_name + "Resource" + api_version.upper()
    param_imports = build_param_imports(client_name, api_version, test_target_data)
    request_imports = build_request_imports(client_name, api_version, test_target_data)
    imports.extend(param_imports)
    imports.extend(request_imports)
    return imports
    # # Request classes
    # for test_target in test_target_data:
    #
    #     if test_target.request_schema_class != "":
    #         # Request class
    #         import_package = import_class_prefix + "Resource" + test_target.request_schema_class.removesuffix("Request")
    #         import_names.append({"importClass": test_target.request_schema_class, "importPackage": import_package})
    #
    #         # Param class
    #         # param_import_class = test_target.request_schema_class.removesuffix("Request") + "Params"
    #         #import_names.append({"importClass": param_import_class, "importPackage": "types"})

    return imports


def dummy_value_for_type(input_type: str):
    """Given a type from the spec, return a default value that can be used as parameter input"""
    # Use faker to produce realistic data?
    # assert input_type in ["array", "boolean", "string", "number"]
    if input_type == "array":
        return "[]"
    elif input_type == "boolean":
        return "true"
    elif input_type == "string":
        return '""'
    elif input_type == "number":
        return "0"
    # "Object" is a special case that deserves further thought
    # elif input_type == "object":
    #     return "null"


def build_dependent_param_string(
    full_spec: dict, dependent_params: list[RequestBodyParameter], include_all=False
) -> str:
    """Builds a 'dependent' object for each item in the input list"""
    dependent_params_strs = []
    for dependent_param in dependent_params:
        # determine the object name
        base_str = get_base_object_from_ref(dependent_param.ref)
        if base_str == "UUID":
            parm_name = camel_case(dependent_param.name)
            parm_name = f"{parm_name[0].lower()}{parm_name[1:]}"
            dependent_params_strs += f'{parm_name}: "{uuid.uuid4()}"'
            continue
        obj_name = f"{base_str[0].lower()}{base_str[1:]}"
        dependent_param_str = f"""const {obj_name} : {base_str} = """
        dependent_params_from_ref = get_request_body_parameters_from_ref(
            full_spec, dependent_param.ref, include_optional=include_all
        )

        # If any of the params are not basic types we need to dive deeper
        dependent_param_str += (
            "{ " + render_params_as_string(full_spec, dependent_params_from_ref) + " };"
        )
        dependent_params_strs.append(dependent_param_str)

    return "".join(dependent_params_strs)


CUSTOM_UUID_REFS = ["#/components/schemas/UUID"]


def build_param_string(
    full_spec: dict,
    req_body_parameters: list[RequestBodyParameter] | None,
    url_parameters: list[URLEmbeddedParameter] | None,
    include_all: bool = False,
) -> (str, str):
    """
    Takes the parameter info from the spec and produces two pieces of information:

    1. generated code to instantiate the request body object (if needed)
    2. a parameter list in string format that can be directly substituted into the template.

    the generated parameter list (#2) will follow a format like the following:
       `<path params>, <request body params>`

    The generated dependent object instantiation code (#1) will look something like this:

    '''
       const someRequestObject: <requestObjectType> = {
           <requestBodyParamName>: <requestBodyParamValue>
       }
    '''

    :param include_all: include all parameters, not just required ones
    :param full_spec object containing all the openapi spec in dict format
    :param req_body_parameters: RequestBodyParameter objects obtained from previous spec parsing
    :param url_parameters: "embedded" parameters for this endpoint, obtained from previous spec parsing
    :return:
    """

    url_param_strs: list[str] = []

    if url_parameters is not None:
        # URL parameters first
        for url_param in url_parameters:
            if url_param.schema.get("$ref", None) in CUSTOM_UUID_REFS:
                url_param_strs.append(f'{url_param.name}: "{uuid.uuid4()}"')
            else:
                url_param_strs.append(
                    f"{url_param.name}: {dummy_value_for_type(url_param.type)}"
                )

    dependent_params = []

    req_param_strs: list[str] = []
    if req_body_parameters is not None:
        # request body parameters next
        for req_body_param in req_body_parameters:
            if req_body_param.ref != "" and req_body_param.ref is not None:
                # If this is a ref we need to build a "dependent" param and put the instance name in the parameter list
                dependent_params.append(req_body_param)
                req_object_name = get_base_object_from_ref(req_body_param.ref)
                # need to lower case the first char
                req_param_strs.append(
                    f"{req_object_name[0].lower()}{req_object_name[1:]}"
                )
            else:
                # custom for our spec
                if req_body_param.ref in CUSTOM_UUID_REFS:
                    req_param_strs.append(f"{req_body_param.name}: '{uuid.uuid4()}'")
                else:
                    if req_body_param.name is not None:
                        req_param_strs.append(
                            f"{req_body_param.name}: {dummy_value_for_type(req_body_param.type)}"
                        )
                    else:
                        # ref is None and name is None
                        req_param_strs.append(
                            f"{dummy_value_for_type(req_body_param.type)}"
                        )

    # handle "dependent" parameters
    # TODO: "normalize" dependent parameters, e.g. dependent parameters that are refs

    dependent_params_str = build_dependent_param_string(full_spec, dependent_params)

    # assemble the final string
    return dependent_params_str, ", ".join(url_param_strs + req_param_strs)


class InvalidInputDataError(Exception):
    pass


def render_params_as_string(full_spec, parameters: list[RequestBodyParameter]) -> str:
    """
    Takes a list of RequestBodyParameter objects and converts it to a string that can be
    substituted into the template for the specific test target.

    List is expected to contain items of primitive types, e.g. non-object
    """
    result = []
    for endpt_param in parameters:
        if endpt_param.type in ["object", None]:
            # Maybe this is the right place to recurse?
            param_string = build_dependent_param_string(full_spec, [endpt_param])
            result.append(param_string)
            continue

        value = dummy_value_for_type(endpt_param.type)

        if endpt_param.name:
            # This is tricky
            name = endpt_param.name
            name = f"{name[0].lower()}{name[1:]}"
            result.append(f"{name}: {value}")
        else:
            result.append(f"{value}")
    return ", ".join(result)


def copy_parameter_data(name: str, parameter_data: dict) -> RequestBodyParameter:
    """Takes request body parameter from the spec and copies it into a RequestBodyParameter object"""
    ref = parameter_data.get("$ref", None)
    unique = parameter_data.get("uniqueItems", False)
    aggregate_info = (
        parameter_data.get("items", None)
        if parameter_data.get("type", None) == "array"
        else None
    )
    return RequestBodyParameter(
        name, parameter_data.get("type", None), ref, unique, aggregate_info
    )


def convert_operation_id_to_classname(name_from_json: str):
    """
    Removes any _ or $ and capitalizes name appropriately; for use in reformatting operationId
    to use in JS import statements
    """
    underscore_idx = name_from_json.index("_")
    temp_str = list(name_from_json)
    temp_str[underscore_idx + 1] = temp_str[underscore_idx + 1].upper()
    return "".join(temp_str).replace("_", "").replace("$", "")


def camel_case(name: str):
    """Takes a string_like_this and converts to StringLikeThis"""
    result = ""
    chunks = name.split("_")
    for chunk in chunks:
        result += chunk[0].upper() + chunk[1 : len(chunk)]
    return result

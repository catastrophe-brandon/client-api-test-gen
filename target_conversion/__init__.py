"""
Code for converting information from the openapi spec into target format for template substitution.
"""

import uuid
from dataclasses import dataclass

from target_conversion.data_modeling import RequestBodyParameter, ApiClientTarget

from target_conversion.ref_handling import (
    get_base_object_from_ref,
    ref_is_basic_type_alias,
)
from target_conversion.ref_handling import get_request_body_parameters_from_ref


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

    dependent_param_str, api_client_param_str, resolved_params = build_param_string(
        full_spec, req_body_parameters, url_parameters, include_all=include_all
    )

    # Each "Request" object has a "Params" object
    parameter_class = (
        (get_base_object_from_ref(parameter_schema).removesuffix("Request") + "Params")
        if parameter_schema != ""
        else ""
    )

    # Grab the response code
    expected_response = "999"
    response_codes = lookup_base["responses"].keys()
    for code in response_codes:
        if code.startswith("2"):
            expected_response = code
            break

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
        expected_response=expected_response,
        resolved_params=resolved_params,
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
                None, None, req_body_schema.get("$ref", None), None, None, None
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
                example=None,
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
    test_target_data: list[ApiClientTarget],
    resolved: list[str],
) -> list[dict]:
    """
    Builds the data to populate the JS imports based on data extracted from the spec
    :returns: a list of string pairs with the name of the class and the name of the source package
    """
    # Client class
    imports = [{"importClass": f"{client_name}Client", "importPackage": "api"}]
    param_imports = build_param_imports(client_name, api_version, test_target_data)
    request_imports = build_request_imports(client_name, api_version, test_target_data)
    imports.extend(param_imports)
    imports.extend(request_imports)
    # Resolved imports should be excluded from the list
    for to_exclude in resolved:
        matching_items = [
            x for x in imports if x.get("importClass", None).startswith(to_exclude)
        ]
        if len(matching_items) > 0:
            imports.remove(matching_items[0])
    return imports


def request_body_parameter_as_string(request_body_param: RequestBodyParameter) -> str:
    """
    Convert RequestBodyParameter object to a string like "name: value"
    :param request_body_param:
    :return:
    """
    if request_body_param.type == "string":
        if request_body_param.example:
            value = f'"{request_body_param.example}"'
        else:
            value = dummy_value_for_type("string")
    else:
        value = dummy_value_for_type(
            request_body_param.type, unique=request_body_param.unique
        )

    if request_body_param.name:
        return f"{request_body_param.name}: {value}"
    else:
        return value


def dummy_value_for_type(input_type: str, unique=False):
    """Given a type from the spec, return a default value that can be used as parameter input"""
    # Use faker to produce realistic data?
    if input_type == "array":
        if unique:
            # Baked-in assumption that arrays are string; might need to rework this later
            return "new Set<string>()"
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
    """Builds a string representation for each item in the input list"""
    dependent_params_strs = []
    for dependent_param in dependent_params:
        # determine the object name
        base_str = get_base_object_from_ref(dependent_param.ref)
        if base_str == "UUID":
            dependent_params_strs += f'{dependent_param.name}: "{uuid.uuid4()}"'
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
) -> (str, str, list[str]):
    """Takes the parameter info extracted from the spec and produces:

    #. generated code to instantiate the request body object(s) (if needed)
    #. a parameter list in string format that can be directly substituted into the template. These are the parameters used directly on the API client invocation call.
    #. a list of any "resolved" classes that do not need to be imported, e.g. LocalTime

    the generated parameter list (#2) will follow a format like the following:
       `<path params>, <request body params>`

    The generated dependent object instantiation code (#1) will look something like this::

       const someRequestObject: <requestObjectType> = {
           <requestBodyParamName>: <requestBodyParamValue>
       }

    :param include_all: include all parameters, not just required ones
    :param full_spec: object containing all the openapi spec in dict format
    :param req_body_parameters: RequestBodyParameter objects obtained from previous spec parsing
    :param url_parameters: "embedded" parameters for this endpoint, obtained from previous spec parsing
    :return:
    """

    url_param_strs: list[str] = []
    resolved: list[str] = []

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

    # request body parameters next
    req_param_strs: list[str] = []
    if req_body_parameters is not None:
        for req_body_param in req_body_parameters:
            if req_body_param.ref != "" and req_body_param.ref is not None:
                if ref_is_basic_type_alias(full_spec, req_body_param.ref):
                    # However, if the ref just points to an alias for a basic type, just resolve
                    # the alias and embed in the parm list
                    resolved_req_body_param = get_request_body_parameters_from_ref(
                        full_spec, req_body_param.ref, include_optional=include_all
                    )
                    # Resolved items do not need to have a class imported
                    resolved.append(get_base_object_from_ref(req_body_param.ref))
                    # Nasty hack to match the generator
                    resolved_req_body_param[0].name = "body"
                    req_param_strs.append(
                        request_body_parameter_as_string(resolved_req_body_param[0])
                    )
                else:
                    # If this is a "real" ref we need to build a "dependent" param and put the
                    # instance name in the parameter list
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
                    # logic to return a typical "name: value" for the parameter
                    req_param_strs.append(
                        request_body_parameter_as_string(req_body_param)
                    )

    dependent_params_str = build_dependent_param_string(
        full_spec, dependent_params, include_all=include_all
    )

    # assemble the final string
    return dependent_params_str, ", ".join(url_param_strs + req_param_strs), resolved


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
            param_string = build_dependent_param_string(full_spec, [endpt_param])
            result.append(param_string)
            continue

        value = request_body_parameter_as_string(endpt_param)
        result.append(value)
    return ", ".join(result)


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

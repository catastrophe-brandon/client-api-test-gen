from target_conversion import RequestBodyParameter


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

    :param full_spec: The full spec data in dict format
    :param ref: The $ref value as a string
    :param include_optional: Flag to include all subfields and not just the required ones
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
            if cur.get("examples", None):
                name = get_base_object_from_ref(ref)
                name = f"{name[0].lower()}{name[1:]}"
                return [
                    RequestBodyParameter(
                        name, cur["type"], None, None, None, cur.get("examples")[0]
                    )
                ]
            else:
                return [RequestBodyParameter(None, cur["type"], None, None, None, None)]

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


def get_base_object_from_ref(ref: str) -> str:
    """Given a $ref returns the name of the object at the end of the ref as a string"""
    split_ref = ref.split("/")
    return split_ref[-1]


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
        name, parameter_data.get("type", None), ref, unique, aggregate_info, None
    )


BASIC_TYPES = ["string", "integer", "number", "boolean", "array"]


def ref_is_basic_type_alias(full_spec: dict, ref: str) -> bool:
    ref_obj = get_ref_from_spec(full_spec, ref)
    if ref_obj.get("type", None) in BASIC_TYPES:
        return True
    return False

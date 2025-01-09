import json
import os
from dataclasses import dataclass
import chevron
import requests


def render_template(file_path, template_data: dict, dest_file=None):
    """Substitutes the data into the mustache template and produces a test file"""
    with open(file_path, "r") as f:
        rendered_template = chevron.render(f, template_data)
        if dest_file:
            with open(dest_file, "w") as output_file:
                json.dump(rendered_template, output_file)
        else:
            # No file? -> stdout
            print(rendered_template)


def convert_to_classname(name_from_json):
    """Removes any _ or $ and capitalizes name appropriately for use in import statements"""
    underscore_idx = name_from_json.index("_")
    temp_str = list(name_from_json)
    temp_str[underscore_idx + 1] = temp_str[underscore_idx + 1].upper()
    return "".join(temp_str).replace("_", "").replace("$", "")


@dataclass
class TestTarget(object):
    """Represents an individual endpoint to be tested based on info taken from the spec"""

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


def get_spec(url) -> dict:
    """Get the openapi spec from a url"""
    resp = requests.get(url)
    return json.loads(resp.text)


def build_imports(import_class_prefix: str, test_target_data: list[TestTarget]) -> list:
    """Builds the data used to populate the imports in the template"""
    # *Response classes
    import_names = [
        f"{import_class_prefix}{x.response_schema_class}"
        for x in test_target_data
        if x.response_schema_class != ""
    ]
    # *Request classes
    import_names.extend(
        [
            f"{import_class_prefix}{y.request_schema_class}"
            for y in test_target_data
            if y.request_schema_class != ""
        ]
    )
    # *Param classes
    import_names.extend(
        [
            f"{import_class_prefix}{z.request_schema_class}Params"
            for z in test_target_data
            if z.request_schema_class != ""
        ]
    )
    return import_names


class SpecDownloadError(Exception):
    pass


def download_specfile(url: str):
    try:
        return get_spec(url)
    except Exception:
        print("Something went wrong while downloading spec from URL")
        raise SpecDownloadError


if __name__ == "__main__":

    example_spec = "https://console.redhat.com/api/notifications/v2/openapi.json"
    try:
        spec = download_specfile(example_spec)
    except SpecDownloadError as e:
        print(f"Error downloading spec from {example_spec}")
        exit(1)

    template_file = "test_template.mustache"
    if not os.path.isfile(template_file):
        print(f"{template_file} is not a file")
        exit(1)

    api_title = spec["info"]["title"]
    api_version = spec["info"]["version"]
    test_targets = []
    for path in spec["paths"]:
        verbs = list(spec["paths"][path].keys())
        for verb in verbs:
            lookup_base = spec["paths"][path][verb]
            try:
                request_schema = lookup_base["requestBody"]["content"][
                    "application/json"
                ]["schema"]["$ref"]
                request_schema_class = request_schema.split("/")[-1]
            except KeyError as ke:
                request_schema = ""
                request_schema_class = ""

            try:
                response_schema = lookup_base["responses"]["200"]["content"][
                    "application/json"
                ]["schema"]["$ref"]
                response_schema_class = response_schema.split("/")[-1]
            except KeyError as ke:
                # print(lookup_base['responses']['200'])
                response_schema = ""
                response_schema_class = ""

            request_class = convert_to_classname(lookup_base["operationId"])

            test_target = TestTarget(
                url_path=path,
                verb=verb,
                summary=lookup_base["summary"],
                operation_id=lookup_base["operationId"],
                request_class=request_class,
                request_schema=request_schema,
                request_schema_class=request_schema_class,
                response_schema=response_schema,
                response_schema_class=response_schema_class,
                parameter_schema="",
            )
            test_targets.append(test_target)

    api_prefix = f"{api_title}{api_version.upper().rstrip('.0')}"
    import_classes = build_imports(api_prefix, test_targets)
    # print(import_classes)

    render_data = {
        "api_title": api_title,
        "api_title_lower": api_title.lower(),
        "api_version": api_version,
        "param_class": import_classes,
        "test_data": [
            {
                "endpoint_summary": test_target.summary,
                "endpoint_operation": test_target.request_class,
                "endpoint_params": f"{test_target.request_class}Params",
            }
            for test_target in test_targets
        ],
    }
    render_template(template_file, render_data)

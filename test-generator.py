import argparse
import os

import chevron

from spec_download import download_specfile, SpecDownloadError
from target_conversion import build_test_target, build_imports, ApiClientTarget


def render_template(file_path, template_data: dict, dest_file: str | None = None):
    """Substitutes the data into the mustache template and produces a test file"""
    with open(file_path, "r") as f:
        rendered_template = chevron.render(f, template_data)
        if dest_file:
            with open(dest_file, "wt") as output_file:
                output_file.write(rendered_template)
        else:
            # No file? -> stdout
            print(rendered_template)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog="test-generator",
        description="Generates test source for use in the javascript-clients repo based on an OpenAPI spec",
        epilog="Never trust an initial query editor",
    )

    parser.add_argument(
        "--spec_url", help="URL of the OpenAPI spec file in JSON format", required=True
    )
    parser.add_argument(
        "--out_file", help="File to write the generated test source to", required=False
    )
    parser.add_argument(
        "--port", help="Destination port for the API client requests", default=3001
    )
    args = parser.parse_args()
    spec_url = args.spec_url.strip("'")
    out_file = args.out_file
    port = args.port

    print(f"Spec url given was: {spec_url}")
    print(f"Output file is: {out_file}")

    print("Downloading spec ...")
    try:
        spec = download_specfile(spec_url)
    except SpecDownloadError as e:
        print(f"Error downloading spec from {spec_url}")
        exit(1)

    template_file = "test_template.mustache"
    if not os.path.isfile(template_file):
        print(f"{template_file} is not a file")
        exit(1)

    api_title = spec["info"]["title"]
    api_version = spec["info"]["version"]
    test_targets: list[ApiClientTarget] = []

    resolved_deps = []
    # Scan through all the paths and verbs building test target info along the way
    for path in spec["paths"]:
        verbs = list(spec["paths"][path].keys())
        for verb in verbs:
            test_tgt_out = build_test_target(spec, path, verb)
            resolved_deps.extend(test_tgt_out.resolved_params)
            test_targets.append(test_tgt_out)

    api_prefix = f"{api_title}Resource{api_version.upper().rstrip('.0')}"
    import_classes = build_imports(
        api_title,
        api_version=f"{api_version.upper().rstrip('.0')}",
        test_target_data=test_targets,
        resolved=resolved_deps,
    )

    print("Rendering the data into the template ...")
    # Render the template with the data extracted from the JSON spec
    render_data = {
        "api_title": api_title,
        "api_title_lower": api_title.lower(),
        "api_version": api_version,
        "import_data": import_classes,
        "port": port,
        "test_data": [
            {
                "endpoint_summary": test_target.summary,
                "endpoint_operation": f"{test_target.request_class[0].lower()}{test_target.request_class[1:]}",
                "endpoint_params": f"{test_target.request_class}Params",
                "endpoint_param_values": test_target.parameter_api_client_call,
                "endpoint_dependent_param_values": test_target.parameter_dependent_objects,
                "expected_response": test_target.expected_response,
            }
            for test_target in test_targets
        ],
    }
    render_template(template_file, render_data, dest_file=out_file)
    if out_file is None:
        print("Success!")
    else:
        print(f"Success! Test source written to {out_file}")

    print("You may want to run a linter or formatter against the generated source")

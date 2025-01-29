# test-generator

CLI to generate API client tests for the javascript-clients repo.

## Setup

Tested locally with python 3.11; your mileage may vary.

```
python -m virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

To send output to a file:

`python -m test-generator spec_url output_file`

To send output to stdout (useful for debugging):

`python -m test-generator spec_url`

## Templating

The generator uses Mustache as the templating engine through the Chevron library.

Template can be found as `test_template.mustache`

The generator essentially gathers a bunch of information from the API spec and transforms it into a format compatible with one specific Mustache template. This means that any changes to the template that add or remove data from the spec require code changes to the generator.

All the necessary data from the API spec is aggregated into a class called TestTarget (for lack of a better name). The logic around data extraction/aggregation is in the `target_conversion` module.

## Tests

Parsing/extraction logic is innately brittle, so tests have been provided in the `tests` module. Whenever the logic changes, update the tests.

Test data is found in the `tests/data` directory. At the moment this only includes an example spec used for testing purposes, but may be expanded to include other data.

Running the tests is as simple as running `pytest`

## Using the output file

The generated output file is Javascript/Typescript source customized to match formatting standards in the javascript-clients repository.

It is intended to be compatible strictly with packages in the javascript-clients repository and no other codebase. One may verify compatibility by copying the produced file to the desired location and running the tests.

The output file includes a single test per client endpoint, thus ensuring a basic level of coverage for each operation. Each test focuses on the "happy path" as a basic sniff test of client operational capability. Test coverage is not intended to be exhaustive, merely an indicator.









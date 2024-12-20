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

`python main.py spec_url output_file`

or

`python main.py spec_url`

if you just want the generated data to go to stdout
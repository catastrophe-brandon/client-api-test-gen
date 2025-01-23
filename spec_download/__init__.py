import json

import requests


def download_specfile(url: str):
    try:
        return get_spec(url)
    except Exception:
        print("Something went wrong while downloading spec from URL")
        raise SpecDownloadError


def get_spec(url) -> dict:
    """Get the openapi spec from an url"""
    resp = requests.get(url)

    if "yaml" in url:
        result = convert_yaml_to_json(resp.text)
    elif "json" in url:
        result = json.loads(resp.text)
    else:
        raise SpecDownloadError

    return result


class SpecDownloadError(Exception):
    pass


def convert_yaml_to_json(file_data: str) -> dict:
    raise NotImplementedError

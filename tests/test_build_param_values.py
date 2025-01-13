import pytest

from main import build_param_values, RequestBodyParameter


def test_build_param_values():
    endpt_jeff = RequestBodyParameter("jeff", "string", True)

    result = build_param_values([endpt_jeff])
    assert result == "Jeff: \"\",\n"

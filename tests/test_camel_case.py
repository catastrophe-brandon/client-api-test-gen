from main import camel_case
import pytest


def test_camel_case():
    example = "This_is_a_test"
    expected = "ThisIsATest"
    assert camel_case(example) == expected

    example2 = "a_b_c_d_e_f"
    assert camel_case(example2) == "ABCDEF"

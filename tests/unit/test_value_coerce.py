from __future__ import annotations

from lib.value_coerce import coerce_number_like


def test_coerce_number_like_handles_int_float_and_strings() -> None:
    assert coerce_number_like(" 42 ") == 42
    assert coerce_number_like("3.14") == 3.14
    assert coerce_number_like(" ") == ""
    assert coerce_number_like("abc") == "abc"
    assert coerce_number_like(123) == 123

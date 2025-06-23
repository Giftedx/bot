from typing import NoReturn
import pytest


def test_exception_handling() -> None:
    """Test various exception handling scenarios."""
    with pytest.raises(ValueError):
        raise ValueError("This is a test exception")

    with pytest.raises(IndexError):
        my_list: list[int] = []
        my_list[1]  # This will raise an IndexError

    with pytest.raises(KeyError):
        my_dict: dict[str, int] = {}
        my_dict["non_existent_key"]  # This will raise a KeyError

    assert True  # Ensure the test runs to completion without unhandled exceptions

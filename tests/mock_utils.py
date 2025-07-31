from typing import Any
from unittest.mock import (
    Mock,
    MagicMock,
)
import inspect


def call_args(mock: Mock | MagicMock) -> dict[str, Any]:
    args, kwargs = mock.call_args
    signature = inspect.signature(mock)
    bound = signature.bind(*args, **kwargs)
    return bound.arguments


def assert_called_once_with(mock: Mock | MagicMock, **_kwargs):
    assert mock.call_count == 1
    bound_args = call_args(mock)
    for key, value in _kwargs.items():
        assert key in bound_args
        assert isinstance(bound_args[key], type(value))
        assert value == bound_args[key]

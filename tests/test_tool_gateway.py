import json

import pytest
from app.core.errors import ToolNotSupportedError
from app.core.settings import get_settings
from app.core.tool_gateway import ToolGateway


def test_normalize_arguments_dict_passthrough() -> None:
    raw = {"query": "foo", "limit": 5}
    assert ToolGateway.normalize_arguments(raw) == raw


def test_normalize_arguments_json_string() -> None:
    raw = json.dumps({"path": "a/b/c.py", "extra": True})
    assert ToolGateway.normalize_arguments(raw) == {"path": "a/b/c.py", "extra": True}


def test_normalize_arguments_invalid_json_empty() -> None:
    assert ToolGateway.normalize_arguments("{not json") == {}


def test_normalize_arguments_other_types_empty() -> None:
    assert ToolGateway.normalize_arguments(None) == {}
    assert ToolGateway.normalize_arguments(123) == {}
    assert ToolGateway.normalize_arguments([]) == {}


def test_execute_unknown_tool_raises() -> None:
    gateway = ToolGateway(settings=get_settings())
    with pytest.raises(ToolNotSupportedError):
        import asyncio

        asyncio.run(gateway.execute(tool_name="does_not_exist", arguments={}))

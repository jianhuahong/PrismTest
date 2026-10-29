from pathlib import Path

import pytest
from runner.core.executor import execute


def test_execute_entry_is_reserved_for_m1():
    with pytest.raises(NotImplementedError):
        execute({"protocol_version": 1})


def test_api_routes_do_not_call_executor():
    root = Path(__file__).resolve().parents[1] / "app" / "api"
    source = "\n".join(path.read_text(encoding="utf-8") for path in root.rglob("*.py"))
    assert "def execute" not in source
    assert "run_task" not in source

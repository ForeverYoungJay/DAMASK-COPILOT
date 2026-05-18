from pathlib import Path

import pytest

from damask_mcp_adapter import validators


def test_validate_workspace_name_accepts_safe_names():
    assert validators.validate_workspace_name("demo_tension") == "demo_tension"


def test_validate_workspace_name_rejects_unsafe_names():
    with pytest.raises(ValueError):
        validators.validate_workspace_name("../bad")


def test_workspace_write_path_stays_inside_workspaces():
    path = validators.ensure_workspace_write_path("demo_tension/test.yaml")
    assert "workspaces" in str(path)


def test_workspace_write_path_rejects_escape():
    with pytest.raises(ValueError):
        validators.ensure_workspace_write_path("/tmp/outside.txt")

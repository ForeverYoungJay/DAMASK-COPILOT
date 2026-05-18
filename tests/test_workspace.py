from pathlib import Path

from damask_mcp_adapter import workspace


def test_project_root_contains_src():
    assert (workspace.project_root() / "src").exists()


def test_workspaces_root_exists():
    assert workspace.workspaces_root().exists()
    assert workspace.workspaces_root().name == "workspaces"

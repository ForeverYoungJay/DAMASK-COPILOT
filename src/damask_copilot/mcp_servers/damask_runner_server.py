"""Thin FastMCP server for DAMASK_grid execution workflows."""

from __future__ import annotations

from damask_copilot.mcp_servers._fastmcp import FastMCP

from damask_mcp_adapter.modules.runner import (
    collect_result_files as collect_result_files_impl,
    find_damask_executables as find_damask_executables_impl,
    list_workspace_files as list_workspace_files_impl,
    run_damask_grid as run_damask_grid_impl,
)

mcp = FastMCP("damask-runner")


@mcp.tool()
def find_damask_executables() -> dict:
    """Find DAMASK_grid executables on PATH and in common local build locations."""
    return find_damask_executables_impl()


@mcp.tool()
def run_damask_grid(
    workspace: str,
    geometry: str,
    load: str,
    material: str,
    timeout_seconds: int = 3600,
) -> dict:
    """Run DAMASK_grid with workspace-local input files using a safe subprocess call."""
    return run_damask_grid_impl(workspace, geometry, load, material, timeout_seconds)


@mcp.tool()
def list_workspace_files(workspace: str) -> dict:
    """List files under a named workspace."""
    return list_workspace_files_impl(workspace)


@mcp.tool()
def collect_result_files(workspace: str) -> dict:
    """Collect result-like files under a named workspace."""
    return collect_result_files_impl(workspace)


if __name__ == "__main__":
    mcp.run()

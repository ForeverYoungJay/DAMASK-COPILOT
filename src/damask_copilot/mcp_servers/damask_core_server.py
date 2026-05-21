"""Thin FastMCP server for DAMASK core inspection workflows."""

from __future__ import annotations

from damask_copilot.mcp_servers._fastmcp import FastMCP

from damask_mcp_adapter.modules.core import (
    check_damask_installation as check_damask_installation_impl,
    get_damask_version as get_damask_version_impl,
    inspect_damask_class as inspect_damask_class_impl,
    inspect_damask_function as inspect_damask_function_impl,
    list_damask_modules as list_damask_modules_impl,
)

mcp = FastMCP("damask-core")


@mcp.tool()
def check_damask_installation() -> dict:
    """Check whether the local DAMASK Python package can be imported."""
    return check_damask_installation_impl()


@mcp.tool()
def get_damask_version() -> dict:
    """Return the local DAMASK Python package version."""
    return get_damask_version_impl()


@mcp.tool()
def list_damask_modules() -> dict:
    """List the main modules and classes exported by DAMASK."""
    return list_damask_modules_impl()


@mcp.tool()
def inspect_damask_class(class_name: str) -> dict:
    """Inspect a DAMASK class exported from the top-level package."""
    return inspect_damask_class_impl(class_name)


@mcp.tool()
def inspect_damask_function(function_name: str) -> dict:
    """Inspect a DAMASK function from the top-level package or main submodules."""
    return inspect_damask_function_impl(function_name)


if __name__ == "__main__":
    mcp.run()

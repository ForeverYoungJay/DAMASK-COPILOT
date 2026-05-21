"""Unified FastMCP server exposing the DAMASK workflow toolchain."""

from __future__ import annotations

from damask_copilot.mcp_servers._fastmcp import FastMCP
from damask_copilot.mcp_servers.damask_core_server import mcp as core_mcp
from damask_copilot.mcp_servers.damask_misc_server import mcp as misc_mcp
from damask_copilot.mcp_servers.damask_postprocess_server import mcp as postprocess_mcp
from damask_copilot.mcp_servers.damask_preprocess_server import mcp as preprocess_mcp
from damask_copilot.mcp_servers.damask_runner_server import mcp as runner_mcp
from damask_copilot.mcp_servers.damask_validation_server import mcp as validation_mcp
from damask_mcp_adapter.api_registry import list_registered_servers

mcp = FastMCP("damask")
mcp.mount(core_mcp)
mcp.mount(preprocess_mcp)
mcp.mount(validation_mcp)
mcp.mount(runner_mcp)
mcp.mount(postprocess_mcp)
mcp.mount(misc_mcp)


@mcp.tool()
def describe_damask_mcp() -> dict:
    """Describe the mounted DAMASK MCP server groups and their registered tools."""
    return list_registered_servers()


def create_server() -> FastMCP:
    """Create the unified DAMASK FastMCP server."""
    return mcp


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

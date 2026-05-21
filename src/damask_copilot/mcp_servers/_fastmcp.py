"""FastMCP compatibility helpers for DAMASK MCP servers."""

from __future__ import annotations

from typing import Any, Callable

try:
    from fastmcp import FastMCP
except ImportError:
    try:
        from mcp.server.fastmcp import FastMCP  # type: ignore[no-redef]
    except ImportError:
        class FastMCP:  # type: ignore[no-redef]
            """Minimal fallback used when FastMCP is not installed in the test environment."""

            def __init__(self, name: str, *args: Any, **kwargs: Any) -> None:
                self.name = name
                self._tools: list[Callable[..., Any]] = []
                self._mounted: list[tuple["FastMCP", str | None]] = []

            def tool(self, *args: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
                def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
                    self._tools.append(fn)
                    return fn

                return decorator

            def mount(
                self,
                server: "FastMCP",
                namespace: str | None = None,
                as_proxy: bool | None = None,
                tool_names: dict[str, str] | None = None,
                prefix: str | None = None,
            ) -> None:
                del as_proxy, tool_names
                self._mounted.append((server, namespace or prefix))

            def run(self, *args: Any, **kwargs: Any) -> None:
                del args, kwargs
                raise RuntimeError(
                    "FastMCP is not installed. Install the project dependencies to run the DAMASK MCP servers."
                )


__all__ = ["FastMCP"]

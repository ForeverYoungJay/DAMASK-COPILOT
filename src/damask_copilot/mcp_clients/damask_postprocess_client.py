"""Placeholder postprocess MCP client interface."""

from __future__ import annotations


class DAMASKPostprocessClient:
    """Future interface to DAMASK postprocess MCP tools."""

    def postprocess(self, *args, **kwargs):
        raise NotImplementedError("DAMASK postprocess MCP integration is not implemented yet.")

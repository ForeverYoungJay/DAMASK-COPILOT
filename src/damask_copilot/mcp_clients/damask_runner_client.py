"""Placeholder runner MCP client interface."""

from __future__ import annotations


class DAMASKRunnerClient:
    """Future interface to DAMASK runner MCP tools."""

    def run(self, *args, **kwargs):
        raise NotImplementedError("DAMASK runner MCP integration is not implemented yet.")

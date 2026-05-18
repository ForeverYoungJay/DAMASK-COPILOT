"""Placeholder runner MCP client interface."""

from __future__ import annotations

from typing import Any

from damask_mcp_adapter.modules.runner import collect_result_files, run_damask_grid


class DAMASKRunnerClient:
    """Thin wrapper around the DAMASK runner adapter."""

    def run(
        self,
        *,
        workspace: str,
        geometry: str,
        load: str,
        material: str,
        timeout_seconds: int = 3600,
    ) -> dict[str, Any]:
        return run_damask_grid(
            workspace=workspace,
            geometry=geometry,
            load=load,
            material=material,
            timeout_seconds=timeout_seconds,
        )

    def collect_results(self, *, workspace: str) -> dict[str, Any]:
        return collect_result_files(workspace)

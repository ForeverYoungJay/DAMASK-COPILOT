"""Placeholder postprocess MCP client interface."""

from __future__ import annotations

from typing import Any

from damask_mcp_adapter.modules.result_tools import export_result_vtk, extract_stress_strain_curve, inspect_result_file


class DAMASKPostprocessClient:
    """Thin wrapper around the DAMASK postprocess adapter."""

    def inspect_result(self, *, path: str) -> dict[str, Any]:
        return inspect_result_file(path)

    def extract_stress_strain(self, *, path: str, output_csv: str) -> dict[str, Any]:
        return extract_stress_strain_curve(path, output_csv)

    def export_vtk(self, *, path: str, output_dir: str) -> dict[str, Any]:
        return export_result_vtk(path, output_dir)

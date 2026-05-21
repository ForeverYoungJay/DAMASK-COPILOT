"""FastMCP server for DAMASK simulation validation workflows."""

from __future__ import annotations

from pathlib import Path

from damask_copilot.mcp_servers._fastmcp import FastMCP
from damask_copilot.tools.geometry import inspect_geometry_material_indices as inspect_geometry_material_indices_impl
from damask_copilot.tools.validation import (
    check_material_indices as check_material_indices_impl,
    check_orientation_format as check_orientation_format_impl,
    check_phase_homogenization_consistency as check_phase_homogenization_consistency_impl,
    check_required_plasticity_parameters as check_required_plasticity_parameters_impl,
    validate_load_yaml as validate_load_yaml_impl,
    validate_material_yaml as validate_material_yaml_impl,
    validate_simulation_setup as validate_simulation_setup_impl,
)
from damask_mcp_adapter.validators import ensure_path_within_workspaces
from damask_mcp_adapter.workspace import workspaces_root

mcp = FastMCP("damask-validation")


def _workspace_path(path: str) -> str:
    candidate_path = Path(path).expanduser()
    if not candidate_path.is_absolute():
        parts = candidate_path.parts
        if parts and parts[0] == workspaces_root().name:
            candidate_path = Path(*parts[1:]) if len(parts) > 1 else Path()
        candidate = workspaces_root() / candidate_path
    else:
        candidate = candidate_path
    return str(ensure_path_within_workspaces(candidate))


@mcp.tool()
def validate_material_yaml_structure(path: str) -> dict:
    """Run deterministic validation checks on a workspace-local material.yaml file."""
    return validate_material_yaml_impl(_workspace_path(path))


@mcp.tool()
def validate_load_yaml_structure(path: str) -> dict:
    """Run deterministic validation checks on a workspace-local load.yaml file."""
    return validate_load_yaml_impl(_workspace_path(path))


@mcp.tool()
def inspect_geometry_material_indices(path: str) -> dict:
    """Inspect geometry material indices from a workspace-local geometry file or metadata stub."""
    return inspect_geometry_material_indices_impl(_workspace_path(path))


@mcp.tool()
def check_phase_homogenization_consistency(material_yaml_path: str) -> dict:
    """Check that material.yaml references existing phase and homogenization definitions."""
    return check_phase_homogenization_consistency_impl(_workspace_path(material_yaml_path))


@mcp.tool()
def check_orientation_format(material_yaml_path: str) -> dict:
    """Check that constituent orientations are quaternion-like numeric vectors of length four."""
    return check_orientation_format_impl(_workspace_path(material_yaml_path))


@mcp.tool()
def check_required_plasticity_parameters(material_yaml_path: str) -> dict:
    """Check that declared plasticity blocks include the minimal required deterministic keys."""
    return check_required_plasticity_parameters_impl(_workspace_path(material_yaml_path))


@mcp.tool()
def check_material_indices(material_yaml_path: str, geometry_path: str) -> dict:
    """Check that geometry material indices do not exceed the material count in material.yaml."""
    return check_material_indices_impl(_workspace_path(material_yaml_path), _workspace_path(geometry_path))


@mcp.tool()
def validate_simulation_setup(material_yaml_path: str, load_yaml_path: str, geometry_path: str) -> dict:
    """Validate material, load, and geometry inputs together before DAMASK execution."""
    return validate_simulation_setup_impl(
        _workspace_path(material_yaml_path),
        _workspace_path(load_yaml_path),
        _workspace_path(geometry_path),
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

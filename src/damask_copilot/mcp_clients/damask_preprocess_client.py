"""Local preprocess client wrapper for DAMASK Copilot."""

from __future__ import annotations

from typing import Any

from damask_mcp_adapter.modules.config_material import create_material_yaml, create_material_yaml_from_template
from damask_mcp_adapter.modules.grid_tools import create_voronoi_grid
from damask_mcp_adapter.modules.loading import (
    create_simple_compression_load_yaml,
    create_simple_tension_load_yaml,
)
from damask_mcp_adapter.modules.grid_tools import inspect_grid
from damask_mcp_adapter.modules.material_tools import add_material_entry, inspect_material_yaml
from damask_mcp_adapter.modules.material_tools import validate_material_yaml as validate_material_yaml_impl
from damask_mcp_adapter.workspace import import_damask
from damask_mcp_adapter.modules.yaml_tools import (
    read_yaml_file as read_yaml_file_impl,
    validate_yaml_file as validate_yaml_file_impl,
    write_yaml_file as write_yaml_file_impl,
)


class DAMASKPreprocessClient:
    """Thin wrapper around the existing local DAMASK preprocess adapter layer."""

    def create_material_yaml(
        self,
        *,
        path: str,
        material_name: str,
        phase_name: str,
        lattice: str,
        elastic: dict,
        plastic: dict | None = None,
    ) -> dict:
        return create_material_yaml(path, material_name, phase_name, lattice, elastic, plastic)

    def create_material_yaml_from_template(
        self,
        *,
        path: str,
        homogenization: dict[str, Any],
        phase: dict[str, Any],
        material: list[dict[str, Any]],
    ) -> dict:
        return create_material_yaml_from_template(path, homogenization, phase, material)

    def create_simple_tension_load_yaml(
        self,
        *,
        path: str,
        strain_rate: float,
        final_strain: float,
        steps: int,
    ) -> dict:
        return create_simple_tension_load_yaml(path, strain_rate, final_strain, steps)

    def create_simple_compression_load_yaml(
        self,
        *,
        path: str,
        strain_rate: float,
        final_strain: float,
        steps: int,
    ) -> dict:
        return create_simple_compression_load_yaml(path, strain_rate, final_strain, steps)

    def create_voronoi_grid(
        self,
        *,
        path: str,
        cells: list[int],
        size: list[float],
        grains: int,
        seed: int = 0,
    ) -> dict:
        return create_voronoi_grid(path, cells, size, grains, seed=seed)

    def inspect_grid(self, *, path: str) -> dict[str, Any]:
        return inspect_grid(path)

    def inspect_material_yaml(self, *, path: str) -> dict[str, Any]:
        return inspect_material_yaml(path)

    def validate_material_yaml(self, *, path: str) -> dict[str, Any]:
        return validate_material_yaml_impl(path)

    def add_material_entry(
        self,
        *,
        path: str,
        homogenization: str,
        phase: str,
        orientation_quaternion: list[float],
        volume_fraction: float = 1.0,
    ) -> dict[str, Any]:
        return add_material_entry(path, homogenization, phase, orientation_quaternion, volume_fraction)

    def create_random_orientations(self, *, count: int, seed: int = 0) -> list[list[float]]:
        damask = import_damask()
        rotations = damask.Rotation.from_random(shape=count, rng_seed=seed)
        quaternions = rotations.as_quaternion().tolist()
        if count == 1 and quaternions and isinstance(quaternions[0], float):
            return [quaternions]
        return quaternions

    def write_yaml_file(self, *, path: str, data: object) -> dict[str, Any]:
        return write_yaml_file_impl(path=path, data=data)

    def read_yaml_file(self, *, path: str) -> dict[str, Any]:
        return read_yaml_file_impl(path)

    def validate_yaml_file(self, *, path: str) -> dict[str, Any]:
        return validate_yaml_file_impl(path)

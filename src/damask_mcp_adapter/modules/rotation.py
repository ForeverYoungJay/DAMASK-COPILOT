"""Compatibility wrappers for rotation preprocessing helpers."""

from __future__ import annotations

from damask_mcp_adapter.modules.rotation_tools import (
    convert_euler_to_quaternion,
    convert_quaternion_to_euler,
    create_random_orientations,
)

__all__ = [
    "convert_euler_to_quaternion",
    "convert_quaternion_to_euler",
    "create_random_orientations",
]

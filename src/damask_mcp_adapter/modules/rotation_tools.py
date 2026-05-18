"""Rotation tools mapped from DAMASK pre-processing docs."""

from __future__ import annotations

import numpy as np

from damask_mcp_adapter.serializers import summarize_array
from damask_mcp_adapter.workspace import import_damask


def create_random_orientations(count: int, seed: int = 0) -> dict:
    """Create random DAMASK orientations and return quaternion summaries."""
    damask = import_damask()
    rotations = damask.Rotation.from_random(shape=count, rng_seed=seed)
    quaternions = rotations.as_quaternion()
    return {
        "ok": True,
        "count": count,
        "seed": seed,
        "summary": summarize_array(quaternions),
    }


def convert_euler_to_quaternion(euler: list[float], degrees: bool = True) -> dict:
    """Convert Bunge Euler angles to a DAMASK quaternion."""
    damask = import_damask()
    rotation = damask.Rotation.from_Euler_angles(np.array(euler, dtype=float), degrees=degrees)
    quaternion = rotation.as_quaternion().tolist()
    return {
        "ok": True,
        "euler": euler,
        "degrees": degrees,
        "quaternion": quaternion,
    }


def convert_quaternion_to_euler(quaternion: list[float], degrees: bool = True) -> dict:
    """Convert a DAMASK quaternion to Bunge Euler angles."""
    damask = import_damask()
    rotation = damask.Rotation.from_quaternion(np.array(quaternion, dtype=float))
    euler = rotation.as_Euler_angles(degrees=degrees).tolist()
    return {
        "ok": True,
        "quaternion": quaternion,
        "degrees": degrees,
        "euler": euler,
    }


__all__ = [
    "convert_euler_to_quaternion",
    "convert_quaternion_to_euler",
    "create_random_orientations",
]

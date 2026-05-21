"""Deterministic validation helpers for DAMASK Copilot inputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from damask_copilot.mcp_clients.damask_preprocess_client import DAMASKPreprocessClient
from damask_copilot.tools.geometry import inspect_geometry_material_indices


def validate_material_yaml(path: str) -> dict[str, Any]:
    """Perform basic structural validation on material.yaml."""
    payload, errors = _load_yaml_mapping(path)
    if payload is None:
        return {"ok": False, "errors": errors, "material_count": 0}

    material_entries = payload.get("material")
    phases = payload.get("phase", {})
    homogenizations = payload.get("homogenization", {})
    result_errors = list(errors)
    warnings: list[str] = []

    if not isinstance(phases, dict) or not phases:
        result_errors.append("material.yaml must define at least one phase entry.")
    if not isinstance(homogenizations, dict) or not homogenizations:
        result_errors.append("material.yaml must define at least one homogenization entry.")
    if not isinstance(material_entries, list) or not material_entries:
        result_errors.append("material.yaml must define a non-empty material list.")

    if isinstance(material_entries, list):
        for index, entry in enumerate(material_entries):
            if not isinstance(entry, dict):
                result_errors.append(f"material[{index}] must be a mapping.")
                continue
            if entry.get("homogenization") not in homogenizations:
                result_errors.append(
                    f"material[{index}] references missing homogenization '{entry.get('homogenization')}'."
                )
            constituents = entry.get("constituents")
            if not isinstance(constituents, list) or not constituents:
                result_errors.append(f"material[{index}] must define at least one constituent.")
                continue
            for constituent_index, constituent in enumerate(constituents):
                phase = constituent.get("phase") if isinstance(constituent, dict) else None
                if phase not in phases:
                    result_errors.append(
                        f"material[{index}].constituents[{constituent_index}] references missing phase '{phase}'."
                    )
                orientation = constituent.get("O") if isinstance(constituent, dict) else None
                if orientation is None:
                    warnings.append(
                        f"material[{index}].constituents[{constituent_index}] does not define orientation 'O'."
                    )

    result = {
        "ok": not result_errors,
        "errors": result_errors,
        "warnings": warnings,
        "material_count": len(material_entries) if isinstance(material_entries, list) else 0,
    }
    mcp_result = _mcp_validate_material_yaml(path)
    if mcp_result is not None:
        result["mcp_validation"] = mcp_result
        if not mcp_result.get("ok", True):
            result["warnings"].append(
                "DAMASK preprocess validation reported additional issues; see result['mcp_validation'] for details."
            )
    return result


def validate_load_yaml(path: str) -> dict[str, Any]:
    """Perform basic structural validation on load.yaml."""
    payload, errors = _load_yaml_mapping(path)
    if payload is None:
        return {"ok": False, "errors": errors}
    result_errors = list(errors)
    loadsteps = payload.get("loadstep")
    if not isinstance(loadsteps, list) or not loadsteps:
        result_errors.append("load.yaml must define a non-empty loadstep list.")
    result = {"ok": not result_errors, "errors": result_errors}
    mcp_result = _mcp_validate_yaml_file(path)
    if mcp_result is not None:
        result["mcp_validation"] = mcp_result
    return result


def check_phase_homogenization_consistency(material_yaml_path: str) -> dict[str, Any]:
    """Check phase and homogenization references in material.yaml."""
    result = validate_material_yaml(material_yaml_path)
    errors = [
        error
        for error in result.get("errors", [])
        if "phase" in error.lower() or "homogenization" in error.lower()
    ]
    return {"ok": not errors, "errors": errors}


def check_material_indices(material_yaml_path: str, geometry_path: str) -> dict[str, Any]:
    """Check that geometry material indices do not exceed material.yaml entries."""
    material_result = validate_material_yaml(material_yaml_path)
    geometry_result = inspect_geometry_material_indices(geometry_path)
    errors: list[str] = []

    if not material_result.get("ok", False):
        errors.extend(material_result.get("errors", []))
    if not geometry_result.get("ok", False):
        errors.extend(geometry_result.get("errors", []))

    material_count = int(material_result.get("material_count", 0))
    max_index = int(geometry_result.get("max_index", 0)) if geometry_result.get("ok") else 0
    if material_count and geometry_result.get("ok") and max_index >= material_count:
        errors.append(
            "Geometry/material mismatch: geometry references material index "
            f"{max_index}, but material.yaml defines only {material_count} material entr"
            f"{'y' if material_count == 1 else 'ies'}. "
            "This would trigger DAMASK errors such as 'material index out of bounds' or "
            "'More materials requested than found in material.yaml'."
        )

    return {
        "ok": not errors,
        "errors": errors,
        "material_count": material_count,
        "geometry_indices": geometry_result.get("unique_indices", []),
    }


def check_orientation_format(material_yaml_path: str) -> dict[str, Any]:
    """Validate constituent orientations in material.yaml."""
    payload, errors = _load_yaml_mapping(material_yaml_path)
    if payload is None:
        return {"ok": False, "errors": errors}

    result_errors = list(errors)
    for material_index, entry in enumerate(payload.get("material", []) or []):
        for constituent_index, constituent in enumerate(entry.get("constituents", []) or []):
            orientation = constituent.get("O")
            if orientation is None:
                continue
            if not isinstance(orientation, list) or len(orientation) != 4:
                result_errors.append(
                    f"material[{material_index}].constituents[{constituent_index}].O must be a quaternion of length 4."
                )
                continue
            if not all(isinstance(value, (int, float)) for value in orientation):
                result_errors.append(
                    f"material[{material_index}].constituents[{constituent_index}].O must contain numeric values."
                )
    return {"ok": not result_errors, "errors": result_errors}


def check_required_plasticity_parameters(material_yaml_path: str) -> dict[str, Any]:
    """Check that any declared plasticity block has at least minimal parameters."""
    payload, errors = _load_yaml_mapping(material_yaml_path)
    if payload is None:
        return {"ok": False, "errors": errors}

    result_errors = list(errors)
    for phase_name, phase_payload in (payload.get("phase") or {}).items():
        mechanical = phase_payload.get("mechanical", {}) if isinstance(phase_payload, dict) else {}
        plastic = mechanical.get("plastic", {}) if isinstance(mechanical, dict) else {}
        if not plastic:
            continue
        if "type" not in plastic:
            result_errors.append(f"phase '{phase_name}' plastic block must define a 'type'.")
    return {"ok": not result_errors, "errors": result_errors}


def validate_simulation_setup(material_yaml_path: str, load_yaml_path: str, geometry_path: str) -> dict[str, Any]:
    """Validate the file-based DAMASK simulation setup prior to execution."""
    errors: list[str] = []
    warnings: list[str] = []
    checks = {
        "material_yaml": validate_material_yaml(material_yaml_path),
        "load_yaml": validate_load_yaml(load_yaml_path),
        "phase_homogenization": check_phase_homogenization_consistency(material_yaml_path),
        "orientation": check_orientation_format(material_yaml_path),
        "plasticity": check_required_plasticity_parameters(material_yaml_path),
        "material_indices": check_material_indices(material_yaml_path, geometry_path),
    }

    for result in checks.values():
        errors.extend(result.get("errors", []))
        warnings.extend(result.get("warnings", []))

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
        "paths": {
            "material_yaml_path": str(material_yaml_path),
            "load_yaml_path": str(load_yaml_path),
            "geometry_path": str(geometry_path),
        },
    }


def validate_damask_inputs(state: Any) -> dict[str, Any]:
    """Run all deterministic validation checks against the current workflow state."""
    material_yaml_path = _state_value(state, "material_yaml_path")
    load_yaml_path = _state_value(state, "load_yaml_path")
    geometry_path = _state_value(state, "geometry_path")

    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, Any] = {}

    if material_yaml_path:
        checks["material_yaml"] = validate_material_yaml(material_yaml_path)
        checks["phase_homogenization"] = check_phase_homogenization_consistency(material_yaml_path)
        checks["orientation"] = check_orientation_format(material_yaml_path)
        checks["plasticity"] = check_required_plasticity_parameters(material_yaml_path)
    else:
        errors.append("material_yaml_path is missing.")

    if load_yaml_path:
        checks["load_yaml"] = validate_load_yaml(load_yaml_path)
    else:
        errors.append("load_yaml_path is missing.")

    if material_yaml_path and geometry_path:
        checks["material_indices"] = check_material_indices(material_yaml_path, geometry_path)
    elif not geometry_path:
        errors.append("geometry_path is missing.")

    for result in checks.values():
        errors.extend(result.get("errors", []))
        warnings.extend(result.get("warnings", []))

    return {"ok": not errors, "errors": errors, "warnings": warnings, "checks": checks}


def _load_yaml_mapping(path: str) -> tuple[dict[str, Any] | None, list[str]]:
    file_path = Path(path)
    if not file_path.exists():
        return None, [f"File does not exist: {path}"]
    try:
        payload = yaml.safe_load(file_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        return None, [f"Failed to parse YAML '{path}': {type(exc).__name__}: {exc}"]
    if not isinstance(payload, dict):
        return None, [f"YAML root must be a mapping: {path}"]
    return payload, []


def _state_value(state: Any, key: str) -> Any:
    if hasattr(state, key):
        return getattr(state, key)
    if hasattr(state, "get"):
        return state.get(key)
    return None


def _mcp_validate_material_yaml(path: str) -> dict[str, Any] | None:
    try:
        return DAMASKPreprocessClient().validate_material_yaml(path=str(path))
    except Exception:
        return None


def _mcp_validate_yaml_file(path: str) -> dict[str, Any] | None:
    try:
        return DAMASKPreprocessClient().validate_yaml_file(path=str(path))
    except Exception:
        return None

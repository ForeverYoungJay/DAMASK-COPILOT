from pathlib import Path

import yaml

from damask_copilot.tools.validation import validate_simulation_setup


def _write_material_yaml(path: Path) -> None:
    payload = {
        "homogenization": {"SX": {"N_constituents": 1, "mechanical": {"type": "pass"}}},
        "phase": {"alpha": {"lattice": "cF", "mechanical": {"elastic": {"type": "Hooke"}}}},
        "material": [{"homogenization": "SX", "constituents": [{"phase": "alpha", "O": [1.0, 0.0, 0.0, 0.0], "v": 1.0}]}],
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _write_load_yaml(path: Path) -> None:
    payload = {
        "loadstep": [
            {
                "discretization": {"t": 20.0, "N": 4},
                "boundary_conditions": {"mechanical": {"dot_F": [[1.0e-3, 0.0, 0.0], [0.0, "x", 0.0], [0.0, 0.0, "x"]]}},
            }
        ]
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_validate_simulation_setup_passes_for_consistent_stub_files(tmp_path):
    material_path = tmp_path / "material.yaml"
    load_path = tmp_path / "load.yaml"
    geometry_path = tmp_path / "geometry.json"
    _write_material_yaml(material_path)
    _write_load_yaml(load_path)
    geometry_path.write_text(
        '{"format":"damask_copilot_stub_geometry_v1","cells":[4,4,4],"size":[1.0,1.0,1.0],"grains":1,"material_indices":[0]}',
        encoding="utf-8",
    )

    result = validate_simulation_setup(str(material_path), str(load_path), str(geometry_path))

    assert result["ok"] is True
    assert result["checks"]["material_yaml"]["ok"] is True
    assert result["checks"]["load_yaml"]["ok"] is True
    assert result["checks"]["material_indices"]["ok"] is True


def test_validate_simulation_setup_flags_geometry_material_mismatch(tmp_path):
    material_path = tmp_path / "material.yaml"
    load_path = tmp_path / "load.yaml"
    geometry_path = tmp_path / "geometry.json"
    _write_material_yaml(material_path)
    _write_load_yaml(load_path)
    geometry_path.write_text(
        '{"format":"damask_copilot_stub_geometry_v1","cells":[4,4,4],"size":[1.0,1.0,1.0],"grains":2,"material_indices":[0,1]}',
        encoding="utf-8",
    )

    result = validate_simulation_setup(str(material_path), str(load_path), str(geometry_path))

    assert result["ok"] is False
    assert any("Geometry/material mismatch" in error for error in result["errors"])

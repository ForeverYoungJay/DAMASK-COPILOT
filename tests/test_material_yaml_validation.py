from pathlib import Path

import yaml

from damask_copilot.tools.validation import validate_material_yaml


def test_valid_material_yaml_passes_basic_validation(tmp_path):
    material_path = tmp_path / "material.yaml"
    payload = {
        "homogenization": {"SX": {"N_constituents": 1, "mechanical": {"type": "pass"}}},
        "phase": {"alpha": {"lattice": "cF", "mechanical": {"elastic": {"type": "Hooke"}}}},
        "material": [{"homogenization": "SX", "constituents": [{"phase": "alpha", "O": [1.0, 0.0, 0.0, 0.0], "v": 1.0}]}],
    }
    material_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_material_yaml(str(material_path))

    assert result["ok"] is True


def test_missing_phase_reference_fails_validation(tmp_path):
    material_path = tmp_path / "material.yaml"
    payload = {
        "homogenization": {"SX": {"N_constituents": 1, "mechanical": {"type": "pass"}}},
        "phase": {"alpha": {"lattice": "cF", "mechanical": {"elastic": {"type": "Hooke"}}}},
        "material": [{"homogenization": "SX", "constituents": [{"phase": "beta", "O": [1.0, 0.0, 0.0, 0.0], "v": 1.0}]}],
    }
    material_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_material_yaml(str(material_path))

    assert result["ok"] is False
    assert any("missing phase" in error.lower() for error in result["errors"])


def test_missing_homogenization_reference_fails_validation(tmp_path):
    material_path = tmp_path / "material.yaml"
    payload = {
        "homogenization": {"SX": {"N_constituents": 1, "mechanical": {"type": "pass"}}},
        "phase": {"alpha": {"lattice": "cF", "mechanical": {"elastic": {"type": "Hooke"}}}},
        "material": [{"homogenization": "Taylor", "constituents": [{"phase": "alpha", "O": [1.0, 0.0, 0.0, 0.0], "v": 1.0}]}],
    }
    material_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    result = validate_material_yaml(str(material_path))

    assert result["ok"] is False
    assert any("missing homogenization" in error.lower() for error in result["errors"])

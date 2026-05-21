import yaml

from damask_copilot.tools.geometry import build_grid_geometry
from damask_copilot.tools.validation import check_material_indices


def test_geometry_material_indices_match_material_yaml(tmp_path):
    material_path = tmp_path / "material.yaml"
    geometry_path = tmp_path / "geometry.vti"
    material_path.write_text(
        yaml.safe_dump(
            {
                "homogenization": {"SX": {"N_constituents": 1, "mechanical": {"type": "pass"}}},
                "phase": {"alpha": {"lattice": "cF", "mechanical": {"elastic": {"type": "Hooke"}}}},
                "material": [{"homogenization": "SX", "constituents": [{"phase": "alpha", "O": [1.0, 0.0, 0.0, 0.0], "v": 1.0}]}],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    build_grid_geometry({"material_indices": [0, 0, 0], "grains": 1}, str(geometry_path))

    result = check_material_indices(str(material_path), str(geometry_path))

    assert result["ok"] is True


def test_geometry_requiring_missing_material_index_fails_with_clear_error(tmp_path):
    material_path = tmp_path / "material.yaml"
    geometry_path = tmp_path / "geometry.vti"
    material_path.write_text(
        yaml.safe_dump(
            {
                "homogenization": {"SX": {"N_constituents": 1, "mechanical": {"type": "pass"}}},
                "phase": {"alpha": {"lattice": "cF", "mechanical": {"elastic": {"type": "Hooke"}}}},
                "material": [{"homogenization": "SX", "constituents": [{"phase": "alpha", "O": [1.0, 0.0, 0.0, 0.0], "v": 1.0}]}],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    build_grid_geometry({"material_indices": [0, 1], "grains": 2}, str(geometry_path))

    result = check_material_indices(str(material_path), str(geometry_path))

    assert result["ok"] is False
    assert any("material index" in error.lower() or "more materials requested" in error.lower() for error in result["errors"])

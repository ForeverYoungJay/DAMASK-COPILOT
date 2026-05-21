from pathlib import Path

import yaml

from damask_copilot.tools.damask_yaml import build_load_yaml, build_material_yaml, build_numerics_yaml
from damask_copilot.tools.validation import validate_material_yaml


def test_build_material_yaml_falls_back_when_mcp_output_is_not_structured_yaml(monkeypatch, tmp_path):
    material_path = tmp_path / "material.yaml"

    def fake_create_material_yaml(self, *, path, **kwargs):
        Path(path).write_text("material", encoding="utf-8")
        return {"ok": True, "path": path}

    monkeypatch.setattr(
        "damask_copilot.mcp_clients.damask_preprocess_client.DAMASKPreprocessClient.create_material_yaml",
        fake_create_material_yaml,
    )

    build_material_yaml({"material_system": "ni3al_l12", "phase_name": "gamma_prime"}, str(material_path))
    payload = yaml.safe_load(material_path.read_text(encoding="utf-8"))

    assert isinstance(payload, dict)
    assert "material" in payload


def test_build_load_yaml_can_use_mcp_preprocess_client(monkeypatch, tmp_path):
    load_path = tmp_path / "load.yaml"

    def fake_create_simple_tension_load_yaml(self, *, path, strain_rate, final_strain, steps):
        Path(path).write_text(
            yaml.safe_dump({"loadstep": [{"discretization": {"N": steps, "t": final_strain / strain_rate}}]}, sort_keys=False),
            encoding="utf-8",
        )
        return {"ok": True, "path": path}

    monkeypatch.setattr(
        "damask_copilot.mcp_clients.damask_preprocess_client.DAMASKPreprocessClient.create_simple_tension_load_yaml",
        fake_create_simple_tension_load_yaml,
    )

    build_load_yaml(
        {"loading_mode": "uniaxial_tension", "strain_rate": 1.0e-3, "final_strain": 0.02, "steps": 5},
        str(load_path),
    )
    payload = yaml.safe_load(load_path.read_text(encoding="utf-8"))

    assert isinstance(payload, dict)
    assert "loadstep" in payload


def test_build_numerics_yaml_falls_back_when_mcp_writer_is_unavailable(monkeypatch, tmp_path):
    numerics_path = tmp_path / "numerics.yaml"

    monkeypatch.setattr(
        "damask_copilot.mcp_clients.damask_preprocess_client.DAMASKPreprocessClient.write_yaml_file",
        lambda self, *, path, data: (_ for _ in ()).throw(RuntimeError("mcp unavailable")),
    )

    build_numerics_yaml({"numerics": {"solver": {"grid": {"N_staggered_iter_max": 12}}}}, str(numerics_path))
    payload = yaml.safe_load(numerics_path.read_text(encoding="utf-8"))

    assert payload["solver"]["grid"]["N_staggered_iter_max"] == 12


def test_validate_material_yaml_includes_optional_mcp_validation(monkeypatch, tmp_path):
    material_path = tmp_path / "material.yaml"
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

    monkeypatch.setattr(
        "damask_copilot.mcp_clients.damask_preprocess_client.DAMASKPreprocessClient.validate_material_yaml",
        lambda self, *, path: {"ok": True, "source": "mcp"},
    )

    result = validate_material_yaml(str(material_path))

    assert result["ok"] is True
    assert result["mcp_validation"]["source"] == "mcp"

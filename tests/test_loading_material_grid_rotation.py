import numpy as np

from damask_mcp_adapter.modules import config_material, grid, loading, rotation


class FakeLoadcaseGrid(dict):
    def save(self, path):
        return None


class FakeConfigMaterial(dict):
    def save(self, path):
        return None


class FakeRotationArray:
    def __init__(self, values):
        self.values = np.asarray(values, dtype=float)

    def as_quaternion(self):
        return self.values

    def as_Euler_angles(self, degrees=True):
        return np.array([0.0, 0.0, 0.0])


class FakeRotation:
    @staticmethod
    def from_random(shape=None, rng_seed=None):
        return FakeRotationArray(np.zeros((shape, 4)))

    @staticmethod
    def from_Euler_angles(values, degrees=True):
        return FakeRotationArray(np.array([1.0, 0.0, 0.0, 0.0]))

    @staticmethod
    def from_quaternion(values):
        return FakeRotationArray(values)


class FakeDamask:
    LoadcaseGrid = FakeLoadcaseGrid
    ConfigMaterial = FakeConfigMaterial
    Rotation = FakeRotation


def test_create_simple_tension_load_yaml(monkeypatch):
    monkeypatch.setattr(loading, "import_damask", lambda: FakeDamask)
    result = loading.create_simple_tension_load_yaml("demo_tension/load.yaml", 1e-3, 0.1, 10)
    assert result["ok"] is True


def test_create_material_yaml(monkeypatch):
    monkeypatch.setattr(config_material, "import_damask", lambda: FakeDamask)
    monkeypatch.setattr(config_material, "inspect_material_yaml", lambda path: {"ok": True, "path": path})
    result = config_material.create_material_yaml(
        "demo_tension/material.yaml",
        "Taylor",
        "Ferrite",
        "cF",
        {"type": "Hooke", "C_11": 1.0},
    )
    assert result["ok"] is True


def test_rotation_wrapper(monkeypatch):
    monkeypatch.setattr(rotation, "create_random_orientations", lambda count, seed=0: {"ok": True, "count": count})
    assert rotation.create_random_orientations(3)["ok"] is True


def test_grid_wrapper(monkeypatch):
    monkeypatch.setattr(grid, "inspect_grid", lambda path: {"ok": True, "path": path})
    assert grid.inspect_grid("workspaces/demo_tension/geometry.vti")["ok"] is True

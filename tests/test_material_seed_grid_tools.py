from pathlib import Path

import numpy as np

from damask_mcp_adapter.modules import grid_tools, material_tools, seed_tools


class FakeConfig(dict):
    def save(self, path):
        Path(path).write_text("material", encoding="utf-8")

    @classmethod
    def load(cls, path):
        return cls({"material": [], "phase": {"p": {}}, "homogenization": {"h": {}}})

    def material_add(self, homogenization=None, phase=None, O=None, v=None):
        return FakeConfig({"material": [{"homogenization": homogenization, "constituents": [{"phase": phase, "O": O, "v": v}]}], "phase": {phase: {}}, "homogenization": {homogenization: {}}})


class FakeGrid:
    def __init__(self):
        self.cells = np.array([2, 2, 2])
        self.size = np.array([1.0, 1.0, 1.0])
        self.N_materials = 2
        self.material = np.zeros((2, 2, 2), dtype=int)

    @classmethod
    def load(cls, path):
        return cls()

    @staticmethod
    def from_Voronoi_tessellation(cells, size, seeds):
        return FakeGrid()

    def save(self, path):
        Path(path).write_text("grid", encoding="utf-8")

    def scale(self, cells):
        return self

    def renumber(self):
        return self

    def clean(self, **kwargs):
        return self


class FakeDamask:
    ConfigMaterial = FakeConfig
    GeomGrid = FakeGrid

    class seeds:
        @staticmethod
        def from_random(size, N_seeds, cells=None, rng_seed=None):
            return np.zeros((N_seeds, 3))


def test_create_empty_material_yaml(monkeypatch):
    monkeypatch.setattr(material_tools, "import_damask", lambda: FakeDamask)
    result = material_tools.create_empty_material_yaml("demo_tension/empty_material.yaml")
    assert result["ok"] is True


def test_add_material_entry(monkeypatch):
    monkeypatch.setattr(material_tools, "import_damask", lambda: FakeDamask)
    result = material_tools.add_material_entry("workspaces/demo_tension/material.yaml", "h", "p", [1, 0, 0, 0], 1.0)
    assert result["ok"] is True


def test_create_random_seeds(monkeypatch):
    monkeypatch.setattr(seed_tools, "create_random_seeds", lambda count, size, seed=0: {"ok": True, "count": count})
    assert seed_tools.create_random_seeds(3, [1, 1, 1], 0)["ok"] is True


def test_scale_grid(monkeypatch):
    monkeypatch.setattr(grid_tools, "import_damask", lambda: FakeDamask)
    result = grid_tools.scale_grid("workspaces/demo_tension/geometry.vti", [2, 2, 2])
    assert result["ok"] is True

from pathlib import Path

import numpy as np

from damask_mcp_adapter.modules import grid_filter_tools, result_tools, table_tools, util_tools


class FakeResult:
    def __init__(self, path):
        self.increments = ["increment_0"]
        self.times = [0.0]
        self.fields = ["F", "P"]

    def list_data(self):
        return ["increment_0", "F"]

    def add_strain(self, *args):
        return None

    def add_equivalent_Mises(self, *args):
        return None

    def add_deviator(self, *args):
        return None

    def add_spherical(self, *args):
        return None

    def add_gradient(self, *args):
        return None

    def add_divergence(self, *args):
        return None

    def add_curl(self, *args):
        return None

    def export_VTK(self, target_dir=None, parallel=False):
        Path(target_dir).mkdir(parents=True, exist_ok=True)
        (Path(target_dir) / "x.vti").write_text("vtk", encoding="utf-8")


class FakeDamask:
    Result = FakeResult

    class util:
        @staticmethod
        def DREAM3D_base_group(path):
            return "Base"

        @staticmethod
        def DREAM3D_cell_data_group(path):
            return "CellData"

        @staticmethod
        def Miller_to_Bravais(uvw=None, hkl=None):
            return np.array([1, 0, -1, 0])

        @staticmethod
        def Bravais_to_Miller(uvtw=None, hkil=None):
            return np.array([1, 0, 0])

    class grid_filters:
        @staticmethod
        def point_to_node(x):
            return np.asarray(x)

        @staticmethod
        def node_to_point(x):
            return np.asarray(x)

        @staticmethod
        def ravel(x, flatten=False):
            return np.asarray(x)

        @staticmethod
        def unravel(x, cells, flatten=False):
            return np.asarray(x)

        @staticmethod
        def coordinates0_valid(x):
            return True

    class Table:
        @staticmethod
        def load(path):
            class T:
                labels = ["a"]
                shapes = {"a": (1,)}
                comments = []

                def __len__(self):
                    return 2

                def get(self, label):
                    return np.array([[1], [2]])

                def rename(self, old, new):
                    return self

                def sort_by(self, labels, ascending=True):
                    return self

                def save(self, path):
                    Path(path).write_text("table", encoding="utf-8")

            return T()


def test_add_strain(monkeypatch):
    monkeypatch.setattr(result_tools, "import_damask", lambda: FakeDamask)
    result = result_tools.add_strain("workspaces/demo_tension/result.hdf5")
    assert result["ok"] is True


def test_inspect_dream3d_base_group(monkeypatch, tmp_path):
    file_path = tmp_path / "file.dream3d"
    file_path.write_text("x", encoding="utf-8")
    monkeypatch.setattr(util_tools, "import_damask", lambda: FakeDamask)
    assert util_tools.inspect_dream3d_base_group(str(file_path))["ok"] is True


def test_grid_ravel(monkeypatch):
    monkeypatch.setattr(grid_filter_tools, "import_damask", lambda: FakeDamask)
    result = grid_filter_tools.grid_ravel([[[1]]])
    assert result["ok"] is True


def test_inspect_table(monkeypatch, tmp_path):
    file_path = tmp_path / "table.txt"
    file_path.write_text("1_a\n1\n", encoding="utf-8")
    monkeypatch.setattr(table_tools, "import_damask", lambda: FakeDamask)
    assert table_tools.inspect_table(str(file_path))["ok"] is True

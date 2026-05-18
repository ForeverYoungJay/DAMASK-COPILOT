from pathlib import Path

from damask_mcp_adapter.modules import result, runner


class FakeResult:
    def __init__(self, path):
        self.version_major = 3
        self.version_minor = 0
        self.structured = True
        self.increments = ["increment_0"]
        self.times = [0.0]
        self.phases = ["p"]
        self.homogenizations = ["h"]
        self.fields = ["F"]
        self.simulation_setup_files = ["load.yaml"]

    def list_data(self):
        return ["increment_0/F"]


class FakeDamask:
    Result = FakeResult


def test_inspect_result_file(monkeypatch, tmp_path):
    file_path = tmp_path / "result.hdf5"
    file_path.write_text("x", encoding="utf-8")
    monkeypatch.setattr(result, "import_damask", lambda: FakeDamask)
    inspected = result.inspect_result_file(str(file_path))
    assert inspected["ok"] is True


def test_find_damask_executables(monkeypatch):
    monkeypatch.setattr(runner, "_candidate_executables", lambda: [Path("/tmp/DAMASK_grid")])
    found = runner.find_damask_executables()
    assert found["ok"] is True
    assert found["count"] == 1

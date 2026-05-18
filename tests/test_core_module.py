from damask_mcp_adapter.modules import core


class FakeRotation:
    """Fake Rotation."""

    def from_random(self):
        return None


class FakeDamask:
    __version__ = "3.0.2"
    __file__ = "/tmp/damask/__init__.py"
    Rotation = FakeRotation


def test_check_damask_installation(monkeypatch):
    monkeypatch.setattr(core, "import_damask", lambda: FakeDamask)
    result = core.check_damask_installation()
    assert result["ok"] is True
    assert result["version"] == "3.0.2"


def test_inspect_damask_class(monkeypatch):
    monkeypatch.setattr(core, "import_damask", lambda: FakeDamask)
    result = core.inspect_damask_class("Rotation")
    assert result["ok"] is True
    assert result["class_name"] == "Rotation"

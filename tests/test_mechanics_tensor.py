from damask_mcp_adapter.modules import mechanics, tensor


class FakeMechanicsModule:
    @staticmethod
    def strain(F, t, m):
        return F

    @staticmethod
    def stress_Cauchy(P, F):
        return P


class FakeTensorModule:
    @staticmethod
    def deviatoric(T):
        return T

    @staticmethod
    def spherical(T, tensor=True):
        return T


class FakeDamask:
    mechanics = FakeMechanicsModule
    tensor = FakeTensorModule


def test_compute_strain(monkeypatch):
    monkeypatch.setattr(mechanics, "import_damask", lambda: FakeDamask)
    result = mechanics.compute_strain([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    assert result["ok"] is True


def test_compute_deviatoric(monkeypatch):
    monkeypatch.setattr(tensor, "import_damask", lambda: FakeDamask)
    result = tensor.compute_deviatoric([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    assert result["ok"] is True

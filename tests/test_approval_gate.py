from damask_copilot.agents.approval_gate import ApprovalGateAgent
from damask_copilot.graph.state import create_initial_state
from damask_copilot.schemas.checker_report import CheckerReport
from damask_copilot.schemas.simulation_plan import GeometrySpec, LoadingSpec, SimulationPlan


def _plan(cells=None):
    return SimulationPlan(
        name="fcc_al_smoke_test",
        summary="Small smoke test.",
        workspace="fcc_al_smoke_test",
        material_id="fcc_al",
        outputs=["stress_strain_curve"],
        geometry=GeometrySpec(grid_type="voronoi", cells=cells or [8, 8, 8], size=[1.0, 1.0, 1.0], grains=8),
        loading=LoadingSpec(mode="uniaxial_tension", direction="x", final_strain=0.02, strain_rate=1.0e-3, steps=5),
    )


def test_approval_gate_dry_run_is_not_required():
    state = create_initial_state(
        user_query="Study FCC aluminum under uniaxial tension",
        mode="dry_run",
        use_llm=False,
        model=None,
        max_iterations=1,
    )
    state["simulation_plan"] = _plan()
    state["checker_report"] = CheckerReport(ok=True, status="passed")

    updated = ApprovalGateAgent().run(state)

    assert updated["approval_status"] == "not_required"


def test_approval_gate_smoke_test_auto_approves_safe_plan():
    state = create_initial_state(
        user_query="Study FCC aluminum under uniaxial tension",
        mode="smoke_test",
        use_llm=False,
        model=None,
        max_iterations=1,
    )
    state["simulation_plan"] = _plan()
    state["checker_report"] = CheckerReport(ok=True, status="passed")

    updated = ApprovalGateAgent().run(state)

    assert updated["approval_status"] == "approved"


def test_approval_gate_full_run_requires_explicit_approval():
    state = create_initial_state(
        user_query="Study FCC aluminum under uniaxial tension",
        mode="full_run",
        use_llm=False,
        model=None,
        max_iterations=1,
    )
    state["simulation_plan"] = _plan()
    state["checker_report"] = CheckerReport(ok=True, status="passed")

    updated = ApprovalGateAgent().run(state)

    assert updated["approval_status"] == "pending"


def test_approval_gate_rejects_when_checker_is_blocked():
    state = create_initial_state(
        user_query="Study FCC aluminum under uniaxial tension",
        mode="smoke_test",
        use_llm=False,
        model=None,
        max_iterations=1,
    )
    state["simulation_plan"] = _plan()
    state["checker_report"] = CheckerReport(ok=False, status="blocked", errors=["unsafe"])

    updated = ApprovalGateAgent().run(state)

    assert updated["approval_status"] == "rejected"

"""Safety policy checks."""

from __future__ import annotations

from damask_copilot.schemas.simulation_plan import SimulationPlan


def enforce_basic_safety(plan: SimulationPlan) -> list[str]:
    """Return safety-policy violations for a simulation plan."""
    errors: list[str] = []
    if any(cell <= 0 for cell in plan.geometry.cells):
        errors.append("Geometry cells must all be positive.")
    if plan.loading.final_strain > 0.5:
        errors.append("Final strain exceeds the deterministic safety threshold of 0.5.")
    if plan.loading.steps > 1000:
        errors.append("Number of loading steps exceeds the deterministic safety threshold.")
    return errors

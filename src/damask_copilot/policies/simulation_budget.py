"""Simulation budget policy."""

from __future__ import annotations

from damask_copilot.schemas.simulation_plan import SimulationPlan


MAX_TOTAL_CELLS = 32 * 32 * 32


def evaluate_budget(plan: SimulationPlan) -> list[str]:
    """Return budget violations for a simulation plan."""
    total_cells = 1
    for cell in plan.geometry.cells:
        total_cells *= cell

    if total_cells > MAX_TOTAL_CELLS:
        return [f"Planned cell count {total_cells} exceeds deterministic budget {MAX_TOTAL_CELLS}."]
    return []

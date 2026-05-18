"""Approval policy placeholder."""

from __future__ import annotations

from damask_copilot.schemas.research_state import ResearchState


def requires_manual_approval(state: ResearchState) -> bool:
    """Placeholder approval hook for future human-in-the-loop controls."""
    return not state.dry_run and state.simulation_plan is not None

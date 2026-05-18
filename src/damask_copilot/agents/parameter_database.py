"""Deterministic material parameter database agent."""

from __future__ import annotations

from pathlib import Path

from damask_copilot.agents.base import BaseAgent
from damask_copilot.memory.parameter_store import ParameterStore
from damask_copilot.schemas.research_state import ResearchState


class ParameterDatabaseAgent(BaseAgent):
    """Load a material entry from the local parameter store."""

    name = "parameter_database"

    def __init__(self, data_dir: Path | None = None, store: ParameterStore | None = None) -> None:
        resolved_data_dir = data_dir or Path("data/materials")
        self.store = store or ParameterStore(data_dir=resolved_data_dir)
        if not self.store.list_ids():
            self.store.load_library()

    def run(self, state: ResearchState) -> ResearchState:
        if state.goal is None:
            raise ValueError("Research goal must be set before loading material data.")

        query = state.goal.material_system
        card = self.store.resolve(query)
        if card is None:
            available = ", ".join(self.store.list_ids())
            raise ValueError(f"No material matched '{query}'. Available material ids: {available}")

        state.selected_material_key = card.material_id
        state.material_card = card.model_copy(deep=True)
        state.status = "material_loaded"
        return self.add_trace(
            state,
            "material_loaded",
            {"material_id": card.material_id, "path": card.source_path},
        )

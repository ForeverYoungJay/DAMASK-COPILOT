"""Deterministic material parameter database agent."""

from __future__ import annotations

from pathlib import Path

import yaml

from damask_copilot.agents.base import BaseAgent
from damask_copilot.schemas.material import MaterialParameterCard
from damask_copilot.schemas.research_state import ResearchState


class ParameterDatabaseAgent(BaseAgent):
    """Load a material entry from local example data."""

    name = "parameter_database"

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or Path("data/materials")

    def run(self, state: ResearchState) -> ResearchState:
        if state.goal is None:
            raise ValueError("Research goal must be set before loading material data.")

        index_path = self.data_dir / "index.yaml"
        with index_path.open("r", encoding="utf-8") as handle:
            index_data = yaml.safe_load(handle) or {}

        materials = index_data.get("materials", {})
        selected_key = state.goal.material_system

        if selected_key not in materials:
            aliases = {
                alias: name
                for name, payload in materials.items()
                for alias in payload.get("aliases", [])
            }
            selected_key = aliases.get(selected_key, next(iter(materials), ""))

        if not selected_key:
            raise ValueError("No material definitions are available in data/materials/index.yaml.")

        entry = materials[selected_key]
        material_path = self.data_dir / entry["file"]
        with material_path.open("r", encoding="utf-8") as handle:
            material_data = yaml.safe_load(handle) or {}

        state.selected_material_key = selected_key
        state.material_card = MaterialParameterCard(
            material_id=selected_key,
            material_name=material_data.get("material_name", selected_key),
            crystal_structure=material_data.get("crystal_structure", "unknown"),
            phase_type=material_data.get("phase_type", "unknown"),
            source_path=str(material_path),
            parameters=material_data,
        )
        state.status = "material_loaded"
        return self.add_trace(
            state,
            "material_loaded",
            {"material_id": selected_key, "path": str(material_path)},
        )

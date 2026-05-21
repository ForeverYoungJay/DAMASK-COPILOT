"""Deprecated material-knowledge micro-agent retained for compatibility wrappers."""

from __future__ import annotations

from damask_copilot.agents.base import BaseAgent
from damask_copilot.agents._deprecation import warn_legacy_agent
from damask_copilot.llm.prompts import load_prompt
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.schemas.llm_outputs import MaterialKnowledgeOutput
from damask_copilot.schemas.research_state import ResearchState


class MaterialKnowledgeAgent(BaseAgent):
    """Deprecated wrapper for material-knowledge aggregation.

    The unified v1 architecture uses `ScientificKnowledgeAgent` instead.
    """

    name = "material_knowledge"

    def __init__(self, *, use_llm: bool = False, model_name: str | None = None, llm_runner: StructuredLLMRunner | None = None) -> None:
        warn_legacy_agent(legacy_name="MaterialKnowledgeAgent", replacement="ScientificKnowledgeAgent")
        self.use_llm = use_llm
        self.model_name = model_name
        self.llm_runner = llm_runner

    def run(self, state: ResearchState) -> ResearchState:
        if self.use_llm or state.use_llm:
            return self._run_llm(state)
        return self._run_deterministic(state)

    def _run_llm(self, state: ResearchState) -> ResearchState:
        material_name = state.material_card.material_name if state.material_card else state.selected_material_key or "unknown"
        parameters = state.material_card.parameters if state.material_card else {}
        runner = self.llm_runner or StructuredLLMRunner(model_name=state.model_name or self.model_name)
        parsed = runner.run_structured(
            prompt_name="material_knowledge",
            system_prompt=load_prompt("material_knowledge"),
            user_prompt=f"User query: {state.user_query}\nMaterial name: {material_name}\nMaterial data: {parameters}",
            output_schema=MaterialKnowledgeOutput,
            model_name=state.model_name or self.model_name,
        )
        state.material_knowledge_output = parsed
        if parsed.knowledge_summary not in state.notes:
            state.notes.append(parsed.knowledge_summary)
        for consideration in parsed.planning_considerations:
            if consideration not in state.notes:
                state.notes.append(consideration)
        state.status = "material_knowledge_added"
        return self.add_trace(state, "material_knowledge_llm", self.model_dump(parsed))

    def _run_deterministic(self, state: ResearchState) -> ResearchState:
        material_name = state.material_card.material_name if state.material_card else state.selected_material_key or "Unknown material"
        crystal_structure = (
            state.material_card.crystal_structure if state.material_card else (state.goal.material_system if state.goal else "unknown")
        )
        notes = list(state.notes)
        evidence_summary = notes[0] if notes else "No literature or experimental context has been summarized yet."
        summary = (
            f"{material_name} is currently handled with deterministic local parameter data. "
            f"Context available so far: {evidence_summary}"
        )
        considerations = [
            "Use a small smoke-test plan before enabling real DAMASK execution.",
            "Keep loading simple and validate all generated plans with deterministic checker rules.",
        ]
        if any("No experimental dataset" in item for item in notes):
            considerations.append("Treat experiment-simulation alignment as optional for this planning pass unless validation becomes a stated goal.")
        if any("not directly relevant" in item.lower() for item in notes):
            considerations.append("Do not treat the current literature inputs as a calibration source; use them only for mechanism framing.")
        state.material_knowledge_output = MaterialKnowledgeOutput(
            material_label=material_name,
            crystal_structure=crystal_structure,
            knowledge_summary=summary,
            planning_considerations=considerations,
        )
        state.notes.append(summary)
        state.status = "material_knowledge_added"
        return self.add_trace(state, "material_knowledge_added", self.model_dump(state.material_knowledge_output))

"""Scientific critic agent."""

from __future__ import annotations

from damask_copilot.agents.base import BaseAgent
from damask_copilot.llm.prompts import load_prompt
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.schemas.critic_report import CriticReport
from damask_copilot.schemas.llm_outputs import ScientificCriticOutput
from damask_copilot.schemas.research_state import ResearchState


class ScientificCriticAgent(BaseAgent):
    """Produce a preliminary deterministic critique."""

    name = "scientific_critic"

    def __init__(self, *, use_llm: bool = False, model_name: str | None = None, llm_runner: StructuredLLMRunner | None = None) -> None:
        self.use_llm = use_llm
        self.model_name = model_name
        self.llm_runner = llm_runner

    def run(self, state: ResearchState) -> ResearchState:
        if self.use_llm or state.use_llm:
            return self._run_llm(state)
        return self._run_deterministic(state)

    def _run_llm(self, state: ResearchState) -> ResearchState:
        runner = self.llm_runner or StructuredLLMRunner(model_name=state.model_name or self.model_name)
        parsed = runner.run_structured(
            prompt_name="scientific_critic",
            system_prompt=load_prompt("scientific_critic"),
            user_prompt=(
                f"User query: {state.user_query}\n"
                f"Goal: {state.goal}\n"
                f"Material card: {state.material_card}\n"
                f"Material knowledge: {state.material_knowledge_output}\n"
                f"Simulation plan: {state.simulation_plan}\n"
                f"Checker report: {state.checker_report}\n"
                f"Run report: {state.run_report}\n"
                f"Postprocess report: {state.postprocess_report}"
            ),
            output_schema=ScientificCriticOutput,
            model_name=state.model_name or self.model_name,
        )
        state.scientific_critic_output = parsed
        state.critic_report = CriticReport(
            summary=parsed.summary,
            strengths=parsed.strengths,
            limitations=parsed.limitations,
            next_steps=parsed.next_steps,
        )
        state.status = "critic_completed"
        return self.add_trace(state, "critic_completed_llm", self.model_dump(parsed))

    def _run_deterministic(self, state: ResearchState) -> ResearchState:
        strengths = [
            "The workflow captures the major research stages from goal parsing to reporting.",
            "The simulation plan is constrained to a small smoke-test budget.",
        ]
        limitations = [
            "Material inference is heuristic and not literature-grounded yet.",
            "DAMASK input generation and execution are placeholders in this pass.",
        ]
        next_steps = [
            "Connect the MCP clients to the input builder, runner, and postprocessor.",
            "Replace heuristic goal parsing with model-backed planning once approved.",
        ]

        if state.postprocess_report and not state.postprocess_report.skipped:
            strengths.append("A result file was available for downstream analysis.")
        else:
            limitations.append("No numerical results were available for scientific interpretation.")

        state.critic_report = CriticReport(
            summary="Preliminary deterministic critique completed.",
            strengths=strengths,
            limitations=limitations,
            next_steps=next_steps,
        )
        state.status = "critic_completed"
        return self.add_trace(state, "critic_completed", {"limitations": len(limitations)})

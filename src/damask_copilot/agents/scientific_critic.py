"""Deprecated scientific-critic micro-agent retained for compatibility wrappers."""

from __future__ import annotations

from damask_copilot.agents.base import BaseAgent
from damask_copilot.agents._deprecation import warn_legacy_agent
from damask_copilot.llm.prompts import load_prompt
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.schemas.critic_report import CriticReport
from damask_copilot.schemas.llm_outputs import ScientificCriticOutput
from damask_copilot.schemas.research_state import ResearchState


class ScientificCriticAgent(BaseAgent):
    """Deprecated wrapper for critique logic.

    The unified v1 architecture uses `AnalysisAndCriticAgent` instead.
    """

    name = "scientific_critic"

    def __init__(self, *, use_llm: bool = False, model_name: str | None = None, llm_runner: StructuredLLMRunner | None = None) -> None:
        warn_legacy_agent(legacy_name="ScientificCriticAgent", replacement="AnalysisAndCriticAgent")
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
        strengths = list(parsed.strengths)
        limitations = list(parsed.limitations)
        next_steps = list(parsed.next_steps)
        summary = parsed.summary

        if state.run_report and state.run_report.status == "success":
            summary = f"Preliminary smoke-test interpretation: {summary}"
            limitations.append("Numerical smoke-test behavior is not yet a validated physical claim.")
        if state.material_card and state.material_card.is_demo_template:
            limitations.append("Demo/template parameters may distort the numerical response.")
        for item in [
            "Verify material.yaml with literature parameters.",
            "Run 16^3 vs 32^3 grid comparison.",
            "Run parameter sensitivity on tau0/h0/n.",
            "Compare with experimental/literature stress-strain data.",
        ]:
            if item not in next_steps:
                next_steps.append(item)
        state.critic_report = CriticReport(
            summary=summary,
            strengths=strengths,
            limitations=limitations,
            next_steps=next_steps,
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

        if state.postprocess_report and state.postprocess_report.status == "success":
            strengths.append("A smoke-test result file was available for downstream analysis.")
            limitations.append("Numerical smoke-test behavior is not yet a validated physical claim.")
        else:
            limitations.append("No numerical results were available for scientific interpretation.")
        if state.material_card and state.material_card.is_demo_template:
            limitations.append("Demo/template parameters may distort the numerical response.")
        next_steps.extend(
            [
                "Verify material.yaml with literature parameters.",
                "Run 16^3 vs 32^3 grid comparison.",
                "Run parameter sensitivity on tau0/h0/n.",
                "Compare with experimental/literature stress-strain data.",
            ]
        )

        state.critic_report = CriticReport(
            summary="Preliminary deterministic smoke-test critique completed." if state.run_report and state.run_report.status == "success" else "Preliminary deterministic critique completed.",
            strengths=strengths,
            limitations=limitations,
            next_steps=next_steps,
        )
        state.status = "critic_completed"
        return self.add_trace(state, "critic_completed", {"limitations": len(limitations)})

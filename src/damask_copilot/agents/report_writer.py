"""Report writer agent."""

from __future__ import annotations

import json
from pathlib import Path

from damask_copilot.agents.base import BaseAgent
from damask_copilot.llm.prompts import load_prompt
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.schemas.llm_outputs import ReportWriterOutput
from damask_copilot.schemas.research_state import ResearchState


class ReportWriterAgent(BaseAgent):
    """Write a markdown report from the research state."""

    name = "report_writer"

    def __init__(self, *, use_llm: bool = False, model_name: str | None = None, llm_runner: StructuredLLMRunner | None = None) -> None:
        self.use_llm = use_llm
        self.model_name = model_name
        self.llm_runner = llm_runner

    def run(self, state: ResearchState) -> ResearchState:
        report_path = self._resolve_report_path(state)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        self.add_trace(state, "report_written", {"report_path": str(report_path)})

        llm_summary = self._llm_summary(state) if (self.use_llm or state.use_llm) else None
        checker_errors = state.checker_report.errors if state.checker_report else []
        checker_warnings = state.checker_report.warnings if state.checker_report else []
        assumptions = state.checker_report.assumptions if state.checker_report else []
        next_steps = list(state.checker_report.next_steps) if state.checker_report else []
        if state.critic_report:
            for item in state.critic_report.next_steps:
                if item not in next_steps:
                    next_steps.append(item)
        if llm_summary:
            for item in llm_summary.next_recommended_simulations:
                if item not in next_steps:
                    next_steps.append(item)
        critique = state.critic_report.summary if state.critic_report else "Critique not available."

        markdown = "\n".join(
            [
                f"# {llm_summary.title if llm_summary else 'DAMASK Copilot Report'}",
                "",
                "## Executive Summary",
                llm_summary.executive_summary if llm_summary else "No LLM executive summary was generated.",
                "",
                "## Key Points",
            ]
            + ([f"- {item}" for item in llm_summary.key_points] if llm_summary and llm_summary.key_points else ["- None"])
            + [
                "",
                "## Research Goal",
                f"- Query: {state.user_query}",
                f"- Objective: {state.goal.objective if state.goal else 'Unknown'}",
                f"- Material system: {state.goal.material_system if state.goal else 'Unknown'}",
                f"- Dry run: {state.dry_run}",
                f"- Use LLM: {state.use_llm}",
                "",
                "## Material Card",
            ]
            + self._material_lines(state)
            + [
                "",
                "## Simulation Plan",
            ]
            + self._plan_lines(state)
            + [
                "",
                "## Generated Files",
            ]
            + self._generated_file_lines(state)
            + [
                "",
                "## Checker Report",
                f"- Passed: {state.checker_report.ok if state.checker_report else False}",
                f"- Errors: {checker_errors or ['None']}",
                f"- Warnings: {checker_warnings or ['None']}",
                "",
                "## Assumptions",
            ]
            + ([f"- {item}" for item in assumptions] if assumptions else ["- None recorded"])
            + [
                "",
                "## Runner",
            ]
            + self._run_lines(state)
            + [
                "",
                "## Post-processing",
            ]
            + self._postprocess_lines(state)
            + [
                "",
                "## Scientific Critique",
                critique,
                "",
                "## Next Recommended Simulations",
            ]
            + ([f"- {item}" for item in next_steps] if next_steps else ["- Review the generated inputs before enabling execution."])
            + [
                "",
                "## Trace",
            ]
            + [f"- {trace.agent}: {trace.event}" for trace in state.traces]
        )

        report_path.write_text(markdown + "\n", encoding="utf-8")
        state.report_markdown = markdown
        state.report_path = str(report_path)
        state.status = "reported"
        return state

    def _resolve_report_path(self, state: ResearchState) -> Path:
        if state.generated_files and state.generated_files.report_path:
            return Path(state.generated_files.report_path)
        if state.simulation_plan:
            return Path("workspaces") / state.simulation_plan.name / "report.md"
        return Path("workspaces") / "damask_copilot_report.md"

    def _material_lines(self, state: ResearchState) -> list[str]:
        if state.material_card is None:
            return ["- None"]
        card = state.material_card
        summary = {
            "material_id": card.material_id,
            "material_name": card.material_name,
            "crystal_structure": card.crystal_structure,
            "phase_type": card.phase_type,
            "confidence": card.confidence,
            "is_demo_template": card.is_demo_template,
        }
        return [
            f"- Selected material: {card.material_name}",
            f"- Material id: {card.material_id}",
            f"- Metadata: `{json.dumps(summary, ensure_ascii=False)}`",
        ]

    def _plan_lines(self, state: ResearchState) -> list[str]:
        if state.simulation_plan is None:
            return ["- None"]
        plan = state.simulation_plan
        return [
            f"- Plan name: {plan.name}",
            f"- Workspace label: {plan.workspace}",
            f"- Summary: {plan.summary}",
            f"- Geometry: {plan.geometry.grid_type}, cells={plan.geometry.cells}, grains={plan.geometry.grains}",
            f"- Loading: {plan.loading.mode} along {plan.loading.direction}, final_strain={plan.loading.final_strain}, steps={plan.loading.steps}",
            f"- Outputs: {plan.outputs or ['None']}",
        ]

    def _generated_file_lines(self, state: ResearchState) -> list[str]:
        if state.generated_files is None:
            return ["- None"]
        files = state.generated_files
        return [
            f"- Workspace: {files.workspace_dir}",
            f"- Material: {files.material_path}",
            f"- Load: {files.load_path}",
            f"- Geometry: {files.geometry_path}",
            f"- Research state: {files.research_state_path}",
            f"- Report: {files.report_path}",
        ]

    def _run_lines(self, state: ResearchState) -> list[str]:
        if state.run_report is None:
            return ["- Status: Runner not reached."]
        report = state.run_report
        return [
            f"- Status: {report.status}",
            f"- Message: {report.message or 'None'}",
            f"- Command: {report.command or 'None'}",
            f"- Return code: {report.returncode if report.returncode is not None else 'None'}",
            f"- Log file: {report.log_file or 'None'}",
            f"- Result files: {report.result_files or ['None']}",
            f"- Started at: {report.started_at or 'None'}",
            f"- Finished at: {report.finished_at or 'None'}",
        ]

    def _postprocess_lines(self, state: ResearchState) -> list[str]:
        if state.postprocess_report is None:
            return ["- Status: Post-processing not reached."]
        report = state.postprocess_report
        return [
            f"- Status: {report.status}",
            f"- Summary: {report.summary}",
            f"- Result file: {report.result_file or 'None'}",
            f"- Inspected fields: {report.inspected_fields or ['None']}",
            f"- Stress-strain CSV: {report.stress_strain_csv or 'None'}",
            f"- VTK dir: {report.vtk_dir or 'None'}",
            f"- Warnings: {report.warnings or ['None']}",
        ]

    def _llm_summary(self, state: ResearchState) -> ReportWriterOutput | None:
        runner = self.llm_runner or StructuredLLMRunner(model_name=state.model_name or self.model_name)
        return runner.run_structured(
            prompt_name="report_writer",
            system_prompt=load_prompt("report_writer"),
            user_prompt=(
                f"User query: {state.user_query}\n"
                f"Goal: {state.goal}\n"
                f"Material card: {state.material_card}\n"
                f"Simulation plan: {state.simulation_plan}\n"
                f"Checker report: {state.checker_report}\n"
                f"Run report: {state.run_report}\n"
                f"Postprocess report: {state.postprocess_report}\n"
                f"Critic report: {state.critic_report}"
            ),
            output_schema=ReportWriterOutput,
            model_name=state.model_name or self.model_name,
        )

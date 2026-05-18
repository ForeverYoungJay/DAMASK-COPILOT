"""Report writer agent."""

from __future__ import annotations

from pathlib import Path

from damask_copilot.agents.base import BaseAgent
from damask_copilot.schemas.research_state import ResearchState


class ReportWriterAgent(BaseAgent):
    """Write a markdown report from the deterministic research state."""

    name = "report_writer"

    def run(self, state: ResearchState) -> ResearchState:
        report_path = self._resolve_report_path(state)
        report_path.parent.mkdir(parents=True, exist_ok=True)

        material_name = state.material_card.material_name if state.material_card else "Unknown"
        plan_name = state.simulation_plan.name if state.simulation_plan else "Not planned"
        checker_ok = state.checker_report.ok if state.checker_report else False
        checker_errors = state.checker_report.errors if state.checker_report else []
        critique = state.critic_report.summary if state.critic_report else "Critique not available."
        run_message = state.run_report.message if state.run_report else "Runner not reached."
        post_summary = (
            state.postprocess_report.summary if state.postprocess_report else "Post-processing not reached."
        )

        markdown = "\n".join(
            [
                "# DAMASK Copilot Report",
                "",
                "## Query",
                state.user_query,
                "",
                "## Goal",
                f"- Objective: {state.goal.objective if state.goal else 'Unknown'}",
                f"- Material system: {state.goal.material_system if state.goal else 'Unknown'}",
                f"- Dry run: {state.dry_run}",
                "",
                "## Material",
                f"- Selected material: {material_name}",
                f"- Material id: {state.selected_material_key or 'Unknown'}",
                "",
                "## Plan",
                f"- Plan name: {plan_name}",
                f"- Workspace: {state.simulation_plan.workspace if state.simulation_plan else 'Unknown'}",
                "",
                "## Checker",
                f"- Passed: {checker_ok}",
                f"- Errors: {checker_errors or ['None']}",
                "",
                "## Runner",
                f"- Status: {run_message}",
                "",
                "## Post-processing",
                f"- Status: {post_summary}",
                "",
                "## Scientific Critique",
                critique,
                "",
                "## Trace",
            ]
            + [f"- {trace.agent}: {trace.event}" for trace in state.traces]
        )

        report_path.write_text(markdown + "\n", encoding="utf-8")
        state.report_markdown = markdown
        state.report_path = str(report_path)
        state.status = "reported"
        return self.add_trace(state, "report_written", {"report_path": str(report_path)})

    def _resolve_report_path(self, state: ResearchState) -> Path:
        if state.generated_files and state.generated_files.report_path:
            return Path(state.generated_files.report_path)
        if state.simulation_plan:
            return Path("workspaces") / state.simulation_plan.workspace / "report.md"
        return Path("workspaces") / "damask_copilot_report.md"

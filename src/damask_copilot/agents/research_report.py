"""Final research report agent for the generic materials research graph."""

from __future__ import annotations

import json
import re
from pathlib import Path

from damask_copilot.graph.materials_research_state import MaterialsResearchState, append_trace
from damask_copilot.llm.prompts import load_prompt
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.schemas.llm_outputs import ReportWriterOutput


class ResearchReportAgent:
    """Write the final generic materials research report."""

    name = "research_report"

    def __init__(
        self,
        *,
        use_llm: bool = False,
        model_name: str | None = None,
        llm_runner: StructuredLLMRunner | None = None,
    ) -> None:
        self.use_llm = use_llm
        self.model_name = model_name
        self.llm_runner = llm_runner

    def run(self, state: MaterialsResearchState) -> MaterialsResearchState:
        report_path = self._resolve_report_path(state)
        report_path.parent.mkdir(parents=True, exist_ok=True)

        literature = dict(state.get("literature_review") or {})
        experimental = dict(state.get("experimental_data_summary") or {})
        strategy = dict(state.get("modeling_strategy") or {})
        project_plan = self._to_jsonable(state.get("project_plan")) or {}
        alignment = dict(state.get("alignment_report") or {})
        if not alignment and experimental.get("status") == "experimental_data_missing":
            alignment = {
                "status": "not_applicable",
                "summary": "No experimental dataset was provided, and experiment-simulation alignment was not required for this planning-oriented case.",
                "compared_observables": [],
                "notes": [],
                "requires_human_review": False,
            }
        parameter_card = state.get("parameter_card")
        critic_report = state.get("critic_report")
        simulation_plan = state.get("simulation_plan")
        llm_summary = self._llm_summary(state) if (self.use_llm or state.get("use_llm", False)) else None

        lines = [
            f"# {llm_summary.title if llm_summary is not None and llm_summary.title else 'DAMASK Copilot Materials Research Report'}",
            "",
        ]
        if llm_summary is not None:
            lines.extend(
                [
                    "## Executive Summary",
                    llm_summary.executive_summary,
                    "",
                    "## Key Points",
                ]
            )
            if llm_summary.key_points:
                lines.extend([f"- {item}" for item in llm_summary.key_points])
            else:
                lines.append("- None")
            lines.append("")
        lines.extend(
            [
                "## Research Question",
                f"- User query: {state.get('user_query')}",
                f"- Research case: `{json.dumps(state.get('research_case') or {}, ensure_ascii=False)}`",
                f"- Research questions: {state.get('research_questions') or ['None']}",
                "",
                "## Literature Evidence",
                f"- Status: {literature.get('status', 'not_available')}",
                f"- Summary: {literature.get('summary') or 'No literature summary available.'}",
                f"- Sources: {self._display_list(literature.get('sources'))}",
                f"- Uncertainty and conflicts: {self._display_list(literature.get('uncertainties'))}",
                "",
                "## Experimental Data Summary",
                *self._render_experimental_summary(experimental),
                "",
                "## Human Feedback History",
            ]
        )
        history = state.get("human_feedback_history", [])
        if history:
            lines.extend([f"- {item}" for item in history])
        else:
            lines.append("- None")
        lines.extend(
            [
                "",
                "## Hypotheses",
            ]
        )
        if state.get("hypotheses"):
            for item in state["hypotheses"]:
                lines.append(f"- {item['id']}: {item['statement']} | expected={item['expected_observable']}")
        else:
            lines.append("- None")
        lines.extend(
            [
                "",
                "## Modeling Strategy",
                f"- Strategy: `{json.dumps(strategy, ensure_ascii=False)}`",
                "",
                "## Project Plan",
                *self._render_project_plan(project_plan, state),
                "",
                "## Parameter Sources",
                *self._render_parameter_sources(parameter_card),
                "",
                "## DAMASK Setup",
                f"- Simulation plan: `{json.dumps(_to_jsonable(simulation_plan), ensure_ascii=False)}`",
                f"- Generated files: `{json.dumps(_to_jsonable(state.get('generated_files')), ensure_ascii=False)}`",
                "",
                "## Results",
                *self._render_run_result(state.get("run_report"), state.get("mode", "dry_run")),
                *self._render_postprocess_result(state.get("postprocess_report"), state.get("mode", "dry_run")),
                "",
                "## Experiment-Simulation Alignment",
                *self._render_alignment_report(alignment),
                "",
                "## Scientific Critique",
                f"- Critic report: `{json.dumps(_to_jsonable(critic_report), ensure_ascii=False)}`",
                "",
                "## Limitations",
            ]
        )
        limitations = list(getattr(critic_report, "limitations", [])) if critic_report is not None else []
        if limitations:
            lines.extend([f"- {item}" for item in limitations])
        else:
            lines.append("- None")
        lines.extend(
            [
                "",
                "## Final Claims and Next Steps",
            ]
        )
        next_steps = list(getattr(critic_report, "next_steps", [])) if critic_report is not None else []
        if llm_summary is not None:
            for item in llm_summary.next_recommended_simulations:
                if item not in next_steps:
                    next_steps.append(item)
        next_steps = self._dedupe_semantic_list(next_steps)
        if next_steps:
            lines.extend([f"- {item}" for item in next_steps])
        else:
            lines.append("- Review the current setup and request another iteration if needed.")

        markdown = "\n".join(lines) + "\n"
        report_path.write_text(markdown, encoding="utf-8")

        updated = dict(state)
        updated["report_path"] = str(report_path)
        updated["final_report"] = markdown
        return append_trace(updated, self.name, "research_report_written", {"report_path": str(report_path)})

    def _resolve_report_path(self, state: MaterialsResearchState) -> Path:
        generated_files = state.get("generated_files")
        report_path = None
        if generated_files is not None:
            report_path = getattr(generated_files, "report_path", None)
            if report_path is None and isinstance(generated_files, dict):
                report_path = generated_files.get("report_path")
        if report_path:
            return Path(report_path)
        workspace = state.get("workspace")
        if workspace:
            return Path(workspace) / "research_report.md"
        return Path("workspaces") / "materials_research_report.md"

    def _llm_summary(self, state: MaterialsResearchState) -> ReportWriterOutput | None:
        try:
            runner = self.llm_runner or StructuredLLMRunner(model_name=state.get("model") or self.model_name)
            return runner.run_structured(
                prompt_name="research_report",
                system_prompt=load_prompt("research_report"),
                user_prompt=(
                    f"User query: {state.get('user_query')}\n"
                    f"Research case: {state.get('research_case')}\n"
                    f"Literature review: {state.get('literature_review')}\n"
                    f"Experimental data summary: {state.get('experimental_data_summary')}\n"
                    f"Project plan: {self._to_jsonable(state.get('project_plan'))}\n"
                    f"Modeling strategy: {state.get('modeling_strategy')}\n"
                    f"Simulation plan: {self._to_jsonable(state.get('simulation_plan'))}\n"
                    f"Run report: {self._to_jsonable(state.get('run_report'))}\n"
                    f"Postprocess report: {self._to_jsonable(state.get('postprocess_report'))}\n"
                    f"Alignment report: {state.get('alignment_report')}\n"
                    f"Scientific critique: {self._to_jsonable(state.get('critic_report'))}"
                ),
                output_schema=ReportWriterOutput,
                model_name=state.get("model") or self.model_name,
            )
        except Exception:
            return None

    @staticmethod
    def _to_jsonable(value):
        if value is None:
            return None
        dumper = getattr(value, "model_dump", None)
        if dumper is not None:
            return dumper()
        if hasattr(value, "dict"):
            return value.dict()
        return value

    def _render_experimental_summary(self, experimental: dict) -> list[str]:
        status = experimental.get("status", "not_available")
        summary = experimental.get("summary") or "No experimental-data summary is available."
        if status == "experimental_data_missing":
            summary = (
                "No experimental datasets were supplied. This is acceptable for exploratory or "
                "hypothesis-driven plans, but it prevents quantitative validation."
            )
        lines = [
            f"- Status: {status}",
            f"- Summary: {summary}",
            f"- Observable candidates: {self._display_list(experimental.get('observable_candidates'))}",
        ]
        semantic_guesses = dict(experimental.get("semantic_column_guesses") or {})
        if semantic_guesses:
            lines.append("- Semantic column guesses:")
            for column, meaning in semantic_guesses.items():
                lines.append(f"  - `{column}` -> `{meaning}`")
        metadata_questions = list(experimental.get("metadata_questions", []) or [])
        if metadata_questions:
            lines.append("- Metadata questions:")
            for item in metadata_questions:
                lines.append(f"  - {item}")
        interpretation_summary = experimental.get("interpretation_summary")
        if interpretation_summary:
            lines.append(f"- Interpretation: {interpretation_summary}")
        return lines

    def _render_parameter_sources(self, parameter_card) -> list[str]:
        payload = _to_jsonable(parameter_card)
        if not isinstance(payload, dict):
            return [f"- Parameter card: `{json.dumps(payload, ensure_ascii=False)}`"]
        parameters = dict(payload.get("parameters") or {})
        source_map = list(parameters.get("parameter_sources", []) or [])
        review_flags = list(parameters.get("review_flags", []) or [])
        assessment = dict(parameters.get("parameter_assessment") or {})

        lines = [
            f"- Material id: {payload.get('material_id', 'unknown')}",
            f"- Material name: {payload.get('material_name', 'unknown')}",
            f"- Confidence: {self._render_parameter_confidence(payload)}",
            f"- Demo/template: {payload.get('is_demo_template', False)}",
            f"- Review flags: {self._display_list(review_flags)}",
        ]
        if source_map:
            lines.append("- Source map:")
            for item in source_map:
                lines.append(
                    f"  - source={item.get('source', 'unknown')}, kind={item.get('kind', 'unknown')}, confidence={item.get('confidence', 'unknown')}"
                )
        if assessment:
            lines.append("- Parameter assessment:")
            if assessment.get("suitability_summary"):
                lines.append(f"  - Summary: {assessment['suitability_summary']}")
            if assessment.get("likely_mismatches"):
                lines.append(f"  - Likely mismatches: {assessment['likely_mismatches']}")
            if assessment.get("assumption_risks"):
                lines.append(f"  - Assumption risks: {assessment['assumption_risks']}")
            if assessment.get("recommended_checks"):
                lines.append(f"  - Recommended checks: {assessment['recommended_checks']}")
            lines.append(f"  - Requires human review: {assessment.get('requires_human_review', False)}")
        else:
            lines.append(f"- Parameter card: `{json.dumps(payload, ensure_ascii=False)}`")
        return lines

    def _render_project_plan(self, project_plan: dict, state: MaterialsResearchState) -> list[str]:
        if not project_plan:
            return [
                "- Status: not_available",
                "- Summary: No project-level plan is available.",
            ]

        lines = [
            f"- Objective: {project_plan.get('project_objective', 'unknown')}",
            f"- Selected simulation id: {state.get('selected_simulation_id') or 'None'}",
            f"- Milestones: {self._display_list(state.get('project_milestones') or [item.get('milestone_id') for item in project_plan.get('milestones', [])])}",
            f"- Current milestone: {state.get('current_milestone') or 'None'}",
            f"- Deliverables: {self._display_list(project_plan.get('deliverables'))}",
            f"- Human review points: {self._display_list(project_plan.get('human_review_points'))}",
            f"- Risks: {self._display_list(project_plan.get('risks'))}",
            f"- Success criteria status: {self._project_success_status(project_plan, state)}",
            f"- Success criteria: {self._display_list(project_plan.get('success_criteria'))}",
            f"- Next action: {project_plan.get('next_action', 'unknown')}",
        ]
        milestones = list(project_plan.get("milestones", []) or [])
        if milestones:
            lines.append("- Milestone details:")
            for item in milestones:
                lines.append(
                    f"  - {item.get('milestone_id', 'unknown')}: {item.get('title', 'untitled')} | deliverables={item.get('deliverables', [])}"
                )
        candidate_simulations = list(project_plan.get("candidate_simulations", []) or [])
        if candidate_simulations:
            lines.append("- Candidate simulations:")
            for item in candidate_simulations:
                lines.append(
                    f"  - {item.get('simulation_id', 'unknown')}: {item.get('title', 'untitled')} | why={item.get('why_needed', 'n/a')}"
                )
        evidence_status = list(project_plan.get("evidence_status", []) or [])
        if evidence_status:
            lines.append("- Evidence status:")
            for item in evidence_status:
                lines.append(
                    f"  - {item.get('topic', 'unknown')}: status={item.get('status', 'unknown')} | summary={item.get('evidence_summary', '')}"
                )
        return lines

    def _render_alignment_report(self, alignment: dict) -> list[str]:
        if not alignment:
            return [
                "- Status: not_available",
                "- Summary: No alignment report is available.",
                "- Compared observables: None",
                "- Requires human review: False",
            ]
        lines = [
            f"- Status: {alignment.get('status', 'not_available')}",
            f"- Summary: {alignment.get('summary') or 'No alignment summary is available.'}",
            f"- Compared observables: {self._display_list(alignment.get('compared_observables'))}",
        ]
        metrics = dict(alignment.get("metrics") or {})
        if metrics:
            lines.append("- Deterministic metrics:")
            for key, value in metrics.items():
                lines.append(f"  - {key}: {value}")
        interpretation = dict(alignment.get("llm_interpretation") or {})
        if interpretation:
            lines.append("- LLM interpretation:")
            if interpretation.get("summary"):
                lines.append(f"  - Summary: {interpretation['summary']}")
            if interpretation.get("likely_mismatch_causes"):
                lines.append(f"  - Likely mismatch causes: {interpretation['likely_mismatch_causes']}")
            if interpretation.get("recommended_actions"):
                lines.append(f"  - Recommended actions: {interpretation['recommended_actions']}")
            if interpretation.get("confidence"):
                lines.append(f"  - Confidence: {interpretation['confidence']}")
        notes = list(alignment.get("notes", []) or [])
        if notes:
            lines.append(f"- Notes: {self._display_list(notes)}")
        lines.append(f"- Requires human review: {alignment.get('requires_human_review', False)}")
        return lines

    def _render_run_result(self, run_report, mode: str) -> list[str]:
        payload = _to_jsonable(run_report)
        if payload is None:
            if mode == "dry_run":
                return [
                    "- Run report status: skipped_due_to_dry_run",
                    "- Run report summary: DAMASK execution was skipped because this run was a dry run.",
                ]
            return [
                "- Run report status: not_available",
                "- Run report summary: No run report is available.",
            ]
        if isinstance(payload, dict):
            return [
                f"- Run report status: {payload.get('status', 'unknown')}",
                f"- Run report summary: returncode={payload.get('returncode', 'unknown')}, results={len(payload.get('result_files', []) or [])}",
            ]
        return [f"- Run report: `{json.dumps(payload, ensure_ascii=False)}`"]

    def _render_postprocess_result(self, postprocess_report, mode: str) -> list[str]:
        payload = _to_jsonable(postprocess_report)
        if payload is None:
            if mode == "dry_run":
                return [
                    "- Postprocess report status: skipped_due_to_dry_run",
                    "- Postprocess report summary: Post-processing was skipped because no simulation run was executed.",
                ]
            return [
                "- Postprocess report status: not_available",
                "- Postprocess report summary: No post-processing report is available.",
            ]
        if isinstance(payload, dict):
            return [
                f"- Postprocess report status: {payload.get('status', 'unknown')}",
                f"- Postprocess report summary: stress_strain_csv={payload.get('stress_strain_csv') or 'None'}, vtk_dir={payload.get('vtk_dir') or 'None'}",
            ]
        return [f"- Postprocess report: `{json.dumps(payload, ensure_ascii=False)}`"]

    def _project_success_status(self, project_plan: dict, state: MaterialsResearchState) -> str:
        if not project_plan.get("success_criteria"):
            return "not_defined"
        alignment = dict(state.get("alignment_report") or {})
        run_report = _to_jsonable(state.get("run_report")) or {}
        if alignment.get("status") == "aligned":
            return "met"
        if run_report.get("status") == "success":
            return "partially_met"
        if state.get("mode") == "dry_run":
            return "not_yet_met (planning_only)"
        return "not_yet_met"

    @staticmethod
    def _display_list(value) -> str:
        if isinstance(value, str):
            return value if value and value != "None" else "None"
        items = [str(item) for item in list(value or []) if item not in {None, "", "None"}]
        return str(items) if items else "None"

    @staticmethod
    def _render_parameter_confidence(payload: dict) -> str:
        confidence = str(payload.get("confidence", "unknown"))
        effective = dict(payload.get("parameters") or {}).get("effective_confidence")
        if effective and effective != confidence:
            return f"{confidence} (effective: {effective} for predictive use)"
        if payload.get("is_demo_template"):
            return f"{confidence} (effective: low for predictive use)"
        return confidence

    @staticmethod
    def _dedupe_semantic_list(items: list[str]) -> list[str]:
        deduped: list[str] = []
        seen: list[str] = []
        for item in items:
            normalized = item.lower()
            normalized = normalized.replace("versus", "vs")
            normalized = re.sub(r"\b(a|an|the)\b", " ", normalized)
            normalized = re.sub(r"[^a-z0-9]+", " ", normalized).strip()
            if not normalized:
                continue
            if normalized in seen:
                continue
            if any(normalized in existing or existing in normalized for existing in seen):
                continue
            seen.append(normalized)
            deduped.append(item)
        return deduped


def _to_jsonable(value):
    if value is None:
        return None
    dumper = getattr(value, "model_dump", None)
    if dumper is not None:
        return dumper()
    if hasattr(value, "dict"):
        return value.dict()
    return value

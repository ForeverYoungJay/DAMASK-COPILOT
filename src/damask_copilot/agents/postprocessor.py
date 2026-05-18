"""Post-processing agent."""

from __future__ import annotations

from pathlib import Path

from damask_copilot.agents.base import BaseAgent
from damask_copilot.mcp_clients.damask_postprocess_client import DAMASKPostprocessClient
from damask_copilot.schemas.postprocess_report import PostprocessReport
from damask_copilot.schemas.research_state import ResearchState


class PostProcessingAgent(BaseAgent):
    """Inspect available results and extract smoke-test outputs."""

    name = "postprocessor"

    def __init__(self, postprocess_client: DAMASKPostprocessClient | None = None) -> None:
        self.postprocess_client = postprocess_client or DAMASKPostprocessClient()

    def run(self, state: ResearchState) -> ResearchState:
        if state.generated_files is None:
            raise ValueError("Generated file paths must be defined before post-processing.")

        if state.run_report is None or state.run_report.status != "success" or not state.run_report.result_files:
            state.postprocess_report = PostprocessReport(
                ok=True,
                status="skipped",
                result_file=None,
                summary="Post-processing skipped because no successful run_report is available.",
            )
            state.status = "postprocess_skipped"
            return self.add_trace(state, "skipped", {"reason": "missing_successful_run"})

        result_file = state.run_report.result_files[0]
        inspect_output = self.postprocess_client.inspect_result(path=result_file)
        inspected_fields = inspect_output.get("fields", []) if inspect_output.get("ok") else []
        stress_strain_csv = Path(state.generated_files.workspace_dir) / "stress_strain.csv"
        vtk_dir = Path(state.generated_files.workspace_dir) / "vtk"
        warnings: list[str] = []

        extract_output = self.postprocess_client.extract_stress_strain(
            path=result_file,
            output_csv=str(stress_strain_csv),
        )
        export_output = self.postprocess_client.export_vtk(
            path=result_file,
            output_dir=str(vtk_dir),
        )
        ok = bool(inspect_output.get("ok"))
        status = "success"
        summary = "Post-processing completed for smoke-test results."
        if not inspect_output.get("ok"):
            ok = False
            status = "failed"
            warnings.append(inspect_output.get("error", "Result inspection failed."))
            summary = "Result inspection failed."
        if not extract_output.get("ok"):
            ok = False
            status = "failed"
            warnings.append(extract_output.get("error", "Stress-strain extraction failed."))
            summary = "Result inspection succeeded, but stress-strain extraction failed."
        if not export_output.get("ok"):
            warnings.append(export_output.get("error", "VTK export failed or is not supported."))

        state.postprocess_report = PostprocessReport(
            ok=ok,
            status=status,
            result_file=result_file,
            inspected_fields=inspected_fields,
            stress_strain_csv=str(stress_strain_csv) if extract_output.get("ok") else None,
            vtk_dir=str(vtk_dir) if export_output.get("ok") else None,
            summary=summary,
            warnings=warnings,
        )
        state.status = "postprocessed"
        return self.add_trace(
            state,
            "postprocessed",
            {"result_file": str(result_file), "status": state.postprocess_report.status, "ok": state.postprocess_report.ok},
        )

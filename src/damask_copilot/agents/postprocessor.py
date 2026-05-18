"""Post-processing agent."""

from __future__ import annotations

from pathlib import Path

from damask_copilot.agents.base import BaseAgent
from damask_copilot.schemas.postprocess_report import PostprocessReport
from damask_copilot.schemas.research_state import ResearchState


class PostProcessingAgent(BaseAgent):
    """Inspect available results and create a placeholder post-processing report."""

    name = "postprocessor"

    def run(self, state: ResearchState) -> ResearchState:
        if state.generated_files is None:
            raise ValueError("Generated file paths must be defined before post-processing.")

        result_file = Path(state.generated_files.result_path)
        if not result_file.exists():
            state.postprocess_report = PostprocessReport(
                ok=True,
                skipped=True,
                result_file=str(result_file),
                derived_files=[],
                summary="Post-processing skipped because no result file exists yet.",
            )
            state.status = "postprocess_skipped"
            return self.add_trace(state, "skipped", {"reason": "missing_result"})

        state.postprocess_report = PostprocessReport(
            ok=True,
            skipped=False,
            result_file=str(result_file),
            derived_files=[],
            summary="Result file detected. Detailed DAMASK post-processing is not implemented yet.",
        )
        state.status = "postprocessed"
        return self.add_trace(state, "postprocessed", {"result_file": str(result_file)})

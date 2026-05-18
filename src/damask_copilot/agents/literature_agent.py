"""Literature-style background agent."""

from __future__ import annotations

from damask_copilot.graph.state import DamaskResearchState, append_trace
from damask_copilot.llm.prompts import load_prompt
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.schemas.llm_outputs import LiteratureAgentOutput


class LiteratureAgent:
    """Generate lightweight literature framing notes without external retrieval."""

    name = "literature_agent"

    def __init__(self, *, use_llm: bool = False, model_name: str | None = None, llm_runner: StructuredLLMRunner | None = None) -> None:
        self.use_llm = use_llm
        self.model_name = model_name
        self.llm_runner = llm_runner

    def run(self, state: DamaskResearchState) -> DamaskResearchState:
        if self.use_llm or state.get("use_llm", False):
            return self._run_llm(state)
        return self._run_deterministic(state)

    def _run_llm(self, state: DamaskResearchState) -> DamaskResearchState:
        runner = self.llm_runner or StructuredLLMRunner(model_name=state.get("model") or self.model_name)
        parsed = runner.run_structured(
            prompt_name="literature_agent",
            system_prompt=load_prompt("literature_agent"),
            user_prompt=(
                f"User query: {state['user_query']}\n"
                f"Research goal: {state.get('research_goal')}\n"
                f"Mode: {state.get('mode')}"
            ),
            output_schema=LiteratureAgentOutput,
            model_name=state.get("model") or self.model_name,
        )
        updated = dict(state)
        updated["literature_notes"] = list(parsed.literature_notes) + [f"Evidence gaps: {', '.join(parsed.evidence_gaps)}"] if parsed.evidence_gaps else list(parsed.literature_notes)
        return append_trace(updated, self.name, "literature_notes_llm", {
            "literature_notes": parsed.literature_notes,
            "evidence_gaps": parsed.evidence_gaps,
        })

    def _run_deterministic(self, state: DamaskResearchState) -> DamaskResearchState:
        notes = [
            "No external literature retrieval was performed in this run.",
            "Use conservative DAMASK smoke-test settings before making physical claims.",
        ]
        updated = dict(state)
        updated["literature_notes"] = notes
        return append_trace(updated, self.name, "literature_notes_added", {"count": len(notes)})

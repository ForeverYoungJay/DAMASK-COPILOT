"""Parameter aggregation agent."""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any

from damask_copilot.graph.materials_research_state import MaterialsResearchState, append_trace
from damask_copilot.llm.prompts import load_prompt
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.memory.parameter_store import ParameterStore
from damask_copilot.schemas.llm_outputs import ParameterAssessmentOutput
from damask_copilot.schemas.material import MaterialParameterCard


class ParameterAgent:
    """Merge internal template parameters with user and literature inputs."""

    name = "parameter_agent"

    def __init__(
        self,
        store: ParameterStore | None = None,
        *,
        use_llm: bool = False,
        model_name: str | None = None,
        llm_runner: StructuredLLMRunner | None = None,
    ) -> None:
        self.store = store or ParameterStore()
        self.use_llm = use_llm
        self.model_name = model_name
        self.llm_runner = llm_runner
        if not self.store.list_ids():
            self.store.load_library()

    def run(self, state: MaterialsResearchState) -> MaterialsResearchState:
        updated = self._run_deterministic(state)
        if self.use_llm or state.get("use_llm", False):
            return self._run_llm(state, updated)
        return updated

    def _run_deterministic(self, state: MaterialsResearchState) -> MaterialsResearchState:
        research_case = dict(state.get("research_case") or {})
        user_constraints = dict(state.get("user_constraints") or {})
        material_key = str(research_case.get("material_system", "generic_material"))

        base_card = self.store.resolve(material_key)
        if base_card is None:
            base_card = MaterialParameterCard(
                material_id=material_key,
                material_name=material_key,
                crystal_structure=str(research_case.get("structure", "unknown")),
                phase_type="unknown",
                source_path="generated",
                confidence="low",
                explicit_assumptions=["No internal material template was available."],
                is_demo_template=True,
                parameters={},
            )

        card = base_card.model_copy(deep=True)
        merged_parameters = deepcopy(card.parameters)
        source_map: list[dict[str, Any]] = [
            {"source": card.source_path, "kind": "internal_template", "confidence": card.confidence}
        ]

        literature_parameters = list(dict(state.get("literature_review") or {}).get("reported_parameters", []))
        for entry in literature_parameters:
            section = entry.get("section")
            values = entry.get("values")
            if section and isinstance(values, dict):
                merged_parameters.setdefault(section, {})
                merged_parameters[section].update(values)
                source_map.append({"source": entry.get("source", "literature"), "kind": "literature", "confidence": entry.get("confidence", "medium")})

        user_parameters = user_constraints.get("parameters", {})
        if isinstance(user_parameters, dict):
            merged_parameters = self._deep_merge(merged_parameters, user_parameters)
            if user_parameters:
                source_map.append({"source": "user_constraints", "kind": "user", "confidence": "high"})

        explicit_assumptions = list(card.explicit_assumptions)
        for item in user_constraints.get("assumptions", []):
            if item not in explicit_assumptions:
                explicit_assumptions.append(item)

        review_flags: list[str] = []
        if card.is_demo_template:
            review_flags.append("template_parameters")
        if card.confidence.lower() == "low":
            review_flags.append("low_confidence")
        if not explicit_assumptions and (card.is_demo_template or card.confidence.lower() == "low"):
            review_flags.append("missing_explicit_assumptions")

        card.parameters = merged_parameters
        card.explicit_assumptions = explicit_assumptions
        card.parameters["parameter_sources"] = source_map
        card.parameters["review_flags"] = review_flags
        card.parameters["effective_confidence"] = "low" if card.is_demo_template else card.confidence

        updated = dict(state)
        updated["parameter_card"] = card
        return append_trace(updated, self.name, "parameter_card_merged", {
            "material_id": card.material_id,
            "review_flags": review_flags,
            "source_count": len(source_map),
        })

    def _run_llm(self, original_state: MaterialsResearchState, summarized_state: MaterialsResearchState) -> MaterialsResearchState:
        parameter_card = summarized_state.get("parameter_card")
        if parameter_card is None:
            return summarized_state

        runner = self.llm_runner or StructuredLLMRunner(model_name=original_state.get("model") or self.model_name)
        parsed = runner.run_structured(
            prompt_name="parameter_agent",
            system_prompt=load_prompt("parameter_agent"),
            user_prompt=(
                f"User query: {original_state.get('user_query')}\n"
                f"Research case: {original_state.get('research_case')}\n"
                f"Modeling strategy: {original_state.get('modeling_strategy')}\n"
                f"Literature review: {original_state.get('literature_review')}\n"
                f"Parameter card: {json.dumps(self._jsonable(parameter_card), ensure_ascii=False)}"
            ),
            output_schema=ParameterAssessmentOutput,
            model_name=original_state.get("model") or self.model_name,
        )

        updated = dict(summarized_state)
        card = parameter_card.model_copy(deep=True) if hasattr(parameter_card, "model_copy") else deepcopy(parameter_card)
        params = getattr(card, "parameters", None) if card is not None else None
        if isinstance(params, dict):
            params["parameter_assessment"] = parsed.model_dump()
            review_flags = list(params.get("review_flags", []))
            if parsed.requires_human_review and "llm_review_required" not in review_flags:
                review_flags.append("llm_review_required")
            for item in parsed.assumption_risks:
                if item and "explicit_assumptions" in card.__dict__ and item not in getattr(card, "explicit_assumptions", []):
                    getattr(card, "explicit_assumptions").append(item)
            params["review_flags"] = review_flags
            card.parameters = params
        updated["parameter_card"] = card
        return append_trace(updated, self.name, "parameter_card_interpreted_llm", {
            "requires_human_review": parsed.requires_human_review,
            "recommended_check_count": len(parsed.recommended_checks),
        })

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        merged = deepcopy(base)
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = self._deep_merge(merged[key], value)
            else:
                merged[key] = deepcopy(value)
        return merged

    @staticmethod
    def _jsonable(value: Any) -> Any:
        if value is None:
            return None
        dumper = getattr(value, "model_dump", None)
        if dumper is not None:
            return dumper()
        if hasattr(value, "dict"):
            return value.dict()
        return value

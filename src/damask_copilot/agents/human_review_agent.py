"""Human-in-the-loop review agent for the materials research graph."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from damask_copilot.graph.materials_research_state import MaterialsResearchState, append_trace

try:
    from langgraph.types import interrupt
except Exception:  # pragma: no cover - graceful fallback for environments without LangGraph runtime
    def interrupt(payload):  # type: ignore[no-redef]
        return {"decision": "pending", "comments": "interrupt() unavailable in the current runtime.", "payload": payload}


class HumanReviewAgent:
    """Request or record human steering, approval, or annotation."""

    name = "human_review"

    def __init__(self, review_stage: str) -> None:
        self.review_stage = review_stage
        self.review_type = {
            "human_review_framing": "steering",
            "human_review_before_run": "approval",
            "human_review_after_critique": "annotation",
        }.get(review_stage, "correction")

    def run(self, state: MaterialsResearchState) -> MaterialsResearchState:
        if not self._review_required(state):
            updated = dict(state)
            updated["pending_human_review"] = None
            if self.review_stage == "human_review_before_run":
                updated["approval_status"] = "not_required" if state.get("mode") == "dry_run" else "approved"
            return append_trace(updated, self.review_stage, "human_review_not_required", {"review_type": self.review_type})

        payload = self._build_payload(state)
        auto_feedback = dict(state.get("user_constraints", {}).get("auto_human_feedback", {}))
        feedback = auto_feedback or interrupt(payload)
        updated = dict(state)
        updated["pending_human_review"] = None
        history = list(updated.get("human_feedback_history", []))
        history.append(
            {
                "stage": self.review_stage,
                "review_type": self.review_type,
                "decision": feedback.get("decision", "pending"),
                "comments": feedback.get("comments", ""),
                "route_hint": feedback.get("route_hint"),
            }
        )
        updated["human_feedback_history"] = history
        if feedback.get("state_patch"):
            updated = self._apply_state_patch(updated, feedback["state_patch"])
        if self.review_stage == "human_review_before_run":
            updated["approval_status"] = self._normalize_approval_decision(feedback.get("decision"))
        elif feedback.get("route_hint"):
            updated["iteration_decision"] = {
                "action": feedback["route_hint"],
                "rationale": "Human reviewer requested an alternate route.",
            }
        return append_trace(updated, self.review_stage, "human_review_recorded", {
            "decision": feedback.get("decision", "pending"),
            "route_hint": feedback.get("route_hint"),
        })

    def _review_required(self, state: MaterialsResearchState) -> bool:
        policy = dict(state.get("human_review_policy") or {})
        if self.review_stage == "human_review_framing":
            project_plan = _model_to_jsonable(state.get("project_plan")) or {}
            return bool(
                policy.get("framing_review")
                or dict(state.get("literature_review") or {}).get("status") == "literature_missing"
                or dict(state.get("experimental_data_summary") or {}).get("needs_human_correction")
                or dict(state.get("modeling_strategy") or {}).get("requires_human_review")
                or bool(project_plan.get("human_review_points"))
            )
        if self.review_stage == "human_review_before_run":
            if state.get("mode") == "dry_run":
                return False
            if state.get("mode") == "full_run":
                return not bool(state.get("user_constraints", {}).get("approve", False))
            review_flags = _parameter_review_flags(state.get("parameter_card"))
            return bool(policy.get("review_low_confidence_parameters") and review_flags)
        if self.review_stage == "human_review_after_critique":
            alignment = dict(state.get("alignment_report") or {})
            critic = state.get("critic_report")
            limitations = list(getattr(critic, "limitations", [])) if critic is not None else []
            experimental = dict(state.get("experimental_data_summary") or {})
            parameter_flags = _parameter_review_flags(state.get("parameter_card"))
            return bool(
                policy.get("after_critique_review")
                or alignment.get("requires_human_review")
                or experimental.get("needs_human_correction")
                or (state.get("mode") == "full_run" and limitations)
                or (state.get("mode") == "full_run" and parameter_flags)
            )
        return False

    def _build_payload(self, state: MaterialsResearchState) -> dict[str, Any]:
        return {
            "stage": self.review_stage,
            "review_type": self.review_type,
            "user_query": state.get("user_query"),
            "research_case": state.get("research_case"),
            "project_plan": _model_to_jsonable(state.get("project_plan")),
            "candidate_simulations": _model_to_jsonable(state.get("candidate_simulations")),
            "selected_simulation_id": state.get("selected_simulation_id"),
            "modeling_strategy": state.get("modeling_strategy"),
            "parameter_review_flags": _parameter_review_flags(state.get("parameter_card")),
            "checker_report": _model_to_jsonable(state.get("checker_report")),
            "critic_report": _model_to_jsonable(state.get("critic_report")),
            "alignment_report": state.get("alignment_report"),
        }

    def _apply_state_patch(self, state: MaterialsResearchState, patch: dict[str, Any]) -> MaterialsResearchState:
        updated = dict(state)
        for key, value in patch.items():
            if isinstance(value, dict) and isinstance(updated.get(key), dict):
                merged = deepcopy(updated[key])
                merged.update(value)
                updated[key] = merged
            else:
                updated[key] = value
        return updated

    @staticmethod
    def _normalize_approval_decision(decision: str | None) -> str:
        lowered = (decision or "").lower()
        if lowered in {"approve", "approved", "yes"}:
            return "approved"
        if lowered in {"reject", "rejected", "no"}:
            return "rejected"
        return "pending"


def _model_to_jsonable(value: Any) -> Any:
    if value is None:
        return None
    dumper = getattr(value, "model_dump", None)
    if dumper is not None:
        return dumper()
    if hasattr(value, "dict"):
        return value.dict()
    return value


def _parameter_review_flags(parameter_card: Any) -> list[str]:
    if parameter_card is None:
        return []
    if isinstance(parameter_card, dict):
        return list(parameter_card.get("parameters", {}).get("review_flags", []))
    return list(getattr(parameter_card, "parameters", {}).get("review_flags", []))

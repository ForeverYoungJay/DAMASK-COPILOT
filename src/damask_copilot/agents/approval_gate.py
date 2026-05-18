"""Deterministic approval gate for LangGraph execution."""

from __future__ import annotations

from damask_copilot.graph.state import DamaskResearchState, append_trace
from damask_copilot.policies.simulation_budget import MAX_TOTAL_CELLS


class ApprovalGateAgent:
    """Decide whether execution is approved, pending, or rejected."""

    name = "approval_gate"

    def run(self, state: DamaskResearchState) -> DamaskResearchState:
        updated = dict(state)
        checker = state.get("checker_report")
        if checker and getattr(checker, "status", None) == "blocked":
            updated["approval_status"] = "rejected"
            return append_trace(updated, self.name, "approval_rejected", {"reason": "checker_blocked"})

        mode = state.get("mode")
        if mode == "dry_run":
            updated["approval_status"] = "not_required"
            return append_trace(updated, self.name, "approval_not_required", {"mode": mode})

        if mode == "smoke_test":
            plan = state.get("simulation_plan")
            total_cells = 1
            if plan is not None:
                for cell in plan.geometry.cells:
                    total_cells *= cell
            if checker and getattr(checker, "ok", False) and total_cells <= MAX_TOTAL_CELLS:
                updated["approval_status"] = "approved"
                return append_trace(updated, self.name, "approval_auto_approved", {"mode": mode, "cells": total_cells})
            updated["approval_status"] = "rejected"
            return append_trace(updated, self.name, "approval_rejected", {"reason": "smoke_test_budget_or_checker"})

        explicit = bool((state.get("approval_request") or {}).get("explicit_approval", False))
        updated["approval_status"] = "approved" if explicit else "pending"
        return append_trace(updated, self.name, f"approval_{updated['approval_status']}", {"mode": mode})

"""Simple optimization helpers for closed-loop parameter updates."""

from __future__ import annotations

from typing import Any


def propose_next_parameters(history: list[dict[str, Any]], objective: dict[str, Any] | None) -> dict[str, Any]:
    """Propose the next parameter set from simple history heuristics."""
    if not history:
        return {"parameters": {}, "reason": "No history was available; keeping the current parameter set."}

    latest = history[-1]
    parameters = dict(latest.get("parameters", {}))
    objective = objective or {}
    scale = float(objective.get("step_scale", 0.95))
    proposed = {
        key: (value * scale if isinstance(value, (int, float)) else value)
        for key, value in parameters.items()
    }
    return {"parameters": proposed, "reason": "Scaled the latest numeric parameter set toward the objective."}


def update_parameter_history(state: Any) -> dict[str, Any]:
    """Append the latest simulation/critique state to parameter history."""
    history = list(_state_value(state, "parameter_history") or [])
    simulation_spec = dict(_state_value(state, "simulation_spec") or {})
    critique = dict(_state_value(state, "critique") or {})
    history.append(
        {
            "iteration": _state_value(state, "iteration") or 0,
            "parameters": dict(simulation_spec.get("parameter_values", {})),
            "objective": critique.get("objective_update"),
            "next_action": _state_value(state, "next_action"),
        }
    )
    return {"parameter_history": history, "latest": history[-1]}


def _state_value(state: Any, key: str) -> Any:
    if hasattr(state, key):
        return getattr(state, key)
    if hasattr(state, "get"):
        return state.get(key)
    return None

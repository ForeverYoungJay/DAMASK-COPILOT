"""Base class for deterministic DAMASK Copilot agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from damask_copilot.schemas.research_state import ResearchState, TraceEvent


class BaseAgent(ABC):
    """Shared interface for all deterministic agents."""

    name: str = "base"

    @abstractmethod
    def run(self, state: ResearchState) -> ResearchState:
        """Apply the agent logic and return the updated state."""

    def add_trace(self, state: ResearchState, event: str, details: dict[str, Any] | None = None) -> ResearchState:
        """Append an agent trace event to the state."""
        payload = TraceEvent(agent=self.name, event=event, details=details or {})
        state.traces.append(payload)
        return state

    @staticmethod
    def model_dump(payload: BaseModel) -> dict[str, Any]:
        """Return a Pydantic model as a plain dictionary across versions."""
        dumper = getattr(payload, "model_dump", None)
        if dumper is not None:
            return dumper()
        return payload.dict()

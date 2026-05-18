"""Experiment memory store."""

from __future__ import annotations

from damask_copilot.schemas.research_state import ResearchState


class ExperimentStore:
    """Minimal in-memory experiment store."""

    def __init__(self) -> None:
        self._items: list[ResearchState] = []

    def add(self, state: ResearchState) -> None:
        self._items.append(state)

    def list(self) -> list[ResearchState]:
        return list(self._items)

"""Result memory store."""

from __future__ import annotations

from damask_copilot.schemas.postprocess_report import PostprocessReport


class ResultStore:
    """Minimal in-memory store for post-processing summaries."""

    def __init__(self) -> None:
        self._items: list[PostprocessReport] = []

    def add(self, report: PostprocessReport) -> None:
        self._items.append(report)

    def list(self) -> list[PostprocessReport]:
        return list(self._items)

"""Experimental data memory store."""

from __future__ import annotations

from typing import Any


class ExperimentStore:
    """Simple in-memory store for experimental datasets and summaries."""

    def __init__(self) -> None:
        self._items: list[dict[str, Any]] = []

    def add(self, record: dict[str, Any]) -> None:
        self._items.append(dict(record))

    def add_summary(
        self,
        *,
        material_system: str | None,
        workflow_type: str | None,
        experimental_data: dict[str, Any] | None,
    ) -> None:
        self.add({
            "material_system": material_system,
            "workflow_type": workflow_type,
            "experimental_data": dict(experimental_data or {}),
        })

    def list(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self._items]

    def find_by_material(self, material_system: str | None) -> list[dict[str, Any]]:
        token = (material_system or "").lower()
        if not token:
            return self.list()
        return [dict(item) for item in self._items if str(item.get("material_system") or "").lower() == token]

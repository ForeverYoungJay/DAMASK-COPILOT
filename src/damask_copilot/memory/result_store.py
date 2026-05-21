"""Simulation result memory store."""

from __future__ import annotations

from typing import Any


class ResultStore:
    """Simple in-memory store for simulation outputs and derived metrics."""

    def __init__(self) -> None:
        self._items: list[dict[str, Any]] = []

    def add(self, record: dict[str, Any]) -> None:
        self._items.append(dict(record))

    def add_result(
        self,
        *,
        material_system: str | None,
        workflow_type: str | None,
        stage: str | None = None,
        simulation_spec: dict[str, Any] | None,
        run_result: dict[str, Any] | None,
        postprocessing_result: dict[str, Any] | None,
        alignment_result: dict[str, Any] | None,
        validation_result: dict[str, Any] | None = None,
        generated_files: dict[str, Any] | None = None,
        critique: dict[str, Any] | None = None,
        next_action: dict[str, Any] | None = None,
        workspace: str | None = None,
    ) -> None:
        self.add({
            "material_system": material_system,
            "workflow_type": workflow_type,
            "stage": stage,
            "simulation_spec": dict(simulation_spec or {}),
            "run_result": dict(run_result or {}),
            "postprocessing_result": dict(postprocessing_result or {}),
            "alignment_result": dict(alignment_result or {}),
            "validation_result": dict(validation_result or {}),
            "generated_files": dict(generated_files or {}),
            "critique": dict(critique or {}),
            "next_action": dict(next_action or {}),
            "workspace": workspace,
        })

    def list(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self._items]

    def find_by_material(self, material_system: str | None) -> list[dict[str, Any]]:
        token = (material_system or "").lower()
        if not token:
            return self.list()
        return [dict(item) for item in self._items if str(item.get("material_system") or "").lower() == token]

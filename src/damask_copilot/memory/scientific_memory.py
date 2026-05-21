"""Shared scientific memory layer for DAMASK Copilot."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from damask_copilot.graph.state import ResearchState
from damask_copilot.memory.experiment_store import ExperimentStore
from damask_copilot.memory.knowledge_graph import MaterialsKnowledgeGraph
from damask_copilot.memory.parameter_store import ParameterStore
from damask_copilot.memory.result_store import ResultStore


class OptimizationHistoryStore:
    """In-memory optimization and calibration history."""

    def __init__(self) -> None:
        self._items: list[dict[str, Any]] = []

    def add(self, record: dict[str, Any]) -> None:
        self._items.append(dict(record))

    def list(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self._items]

    def find_by_material(self, material_system: str | None) -> list[dict[str, Any]]:
        token = (material_system or "").lower()
        if not token:
            return self.list()
        return [dict(item) for item in self._items if str(item.get("material_system") or "").lower() == token]


class ErrorFixStore:
    """In-memory database of common failures and the applied repair actions."""

    def __init__(self) -> None:
        self._items: list[dict[str, Any]] = []

    def add(self, record: dict[str, Any]) -> None:
        self._items.append(dict(record))

    def list(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self._items]

    def find_by_error(self, token: str) -> list[dict[str, Any]]:
        lowered = token.lower()
        return [
            dict(item)
            for item in self._items
            if lowered in str(item.get("error") or "").lower() or lowered in str(item.get("failure_category") or "").lower()
        ]


class DAMASKTemplateStore:
    """File-backed view over reusable DAMASK material/input templates from the demo dataset."""

    def __init__(self, *, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or Path("data/materials")

    def list_templates(self) -> list[dict[str, Any]]:
        templates: list[dict[str, Any]] = []
        index_path = self.data_dir / "index.yaml"
        payload = yaml.safe_load(index_path.read_text(encoding="utf-8")) if index_path.exists() else {}
        for material_id, entry in dict((payload or {}).get("materials", {})).items():
            material_path = self.data_dir / str(entry.get("file", ""))
            if not material_path.exists():
                continue
            material_payload = yaml.safe_load(material_path.read_text(encoding="utf-8")) or {}
            templates.append({
                "material_id": material_id,
                "path": str(material_path),
                "aliases": list(entry.get("aliases", [])),
                "is_demo_template": bool(dict(material_payload.get("metadata") or {}).get("is_demo_template", False)),
                "phase_type": material_payload.get("phase_type"),
            })
        return templates


class ScientificMemoryLayer:
    """Shared infrastructure layer spanning literature, data, templates, results, and graph memory."""

    def __init__(
        self,
        *,
        materials_dir: Path | None = None,
        workspace_root: Path | None = None,
        parameter_store: ParameterStore | None = None,
        experiment_store: ExperimentStore | None = None,
        result_store: ResultStore | None = None,
        optimization_history: OptimizationHistoryStore | None = None,
        error_fix_store: ErrorFixStore | None = None,
        template_store: DAMASKTemplateStore | None = None,
        knowledge_graph: MaterialsKnowledgeGraph | None = None,
    ) -> None:
        resolved_materials_dir = materials_dir or Path("data/materials")
        self.workspace_root = Path(workspace_root or Path("workspaces"))
        self.parameter_store = parameter_store or ParameterStore(data_dir=resolved_materials_dir)
        if not self.parameter_store.list_ids():
            self.parameter_store.load_library()
        self.experiment_store = experiment_store or ExperimentStore()
        self.result_store = result_store or ResultStore()
        self.optimization_history = optimization_history or OptimizationHistoryStore()
        self.error_fix_store = error_fix_store or ErrorFixStore()
        self.template_store = template_store or DAMASKTemplateStore(data_dir=resolved_materials_dir)
        self.knowledge_graph = knowledge_graph or MaterialsKnowledgeGraph(
            data_dir=resolved_materials_dir,
            parameter_store=self.parameter_store,
        )

    def collect_context(self, *, material_system: str | None, workflow_type: str | None = None) -> dict[str, Any]:
        return {
            "literature_memory": self._literature_memory(material_system),
            "cp_parameter_database": self._parameter_database(material_system),
            "damask_input_templates": self.template_store.list_templates(),
            "simulation_result_database": self.result_store.find_by_material(material_system) or self._workspace_simulation_records(material_system),
            "experimental_data_database": self.experiment_store.find_by_material(material_system),
            "optimization_history": self.optimization_history.find_by_material(material_system),
            "error_fix_database": self.error_fix_store.list(),
            "materials_knowledge_graph": self.knowledge_graph.get_material_context(material_system),
            "workflow_type": workflow_type,
        }

    def remember_knowledge_context(self, state: ResearchState) -> None:
        self.experiment_store.add_summary(
            material_system=state.material_system,
            workflow_type=state.workflow_type,
            experimental_data=state.experimental_data,
        )

    def remember_simulation_design(self, state: ResearchState) -> None:
        self.result_store.add_result(
            material_system=state.material_system,
            workflow_type=state.workflow_type,
            stage="design",
            simulation_spec=state.simulation_spec,
            run_result=None,
            postprocessing_result=None,
            alignment_result=None,
            validation_result=state.validation_result,
            generated_files=self._to_jsonable(state.generated_files),
            critique=None,
            next_action=None,
            workspace=state.workspace,
        )

    def remember_analysis(self, state: ResearchState) -> None:
        self.result_store.add_result(
            material_system=state.material_system,
            workflow_type=state.workflow_type,
            stage="analysis",
            simulation_spec=state.simulation_spec,
            run_result=state.run_result,
            postprocessing_result=state.postprocessing_result,
            alignment_result=state.alignment_result,
            validation_result=state.validation_result,
            generated_files=self._to_jsonable(state.generated_files),
            critique=state.critique,
            next_action=state.next_action,
            workspace=state.workspace,
        )
        for item in state.parameter_history:
            record = dict(item)
            record.setdefault("material_system", state.material_system)
            record.setdefault("workflow_type", state.workflow_type)
            self.optimization_history.add(record)
        critique = dict(state.critique or {})
        if critique.get("objective_update"):
            self.optimization_history.add({
                "material_system": state.material_system,
                "workflow_type": state.workflow_type,
                "iteration": state.iteration,
                "objective": critique.get("objective_update"),
                "next_action": state.next_action,
            })
        run_result = dict(state.run_result or {})
        if run_result.get("status") in {"failed", "not_available"}:
            self.error_fix_store.add({
                "material_system": state.material_system,
                "workflow_type": state.workflow_type,
                "failure_category": run_result.get("failure_category"),
                "error": run_result.get("error") or run_result.get("message"),
                "suggested_fix": (state.next_action or {}).get("reason"),
            })
        validation = dict(state.validation_result or {})
        for error in validation.get("errors", []) or []:
            self.error_fix_store.add({
                "material_system": state.material_system,
                "workflow_type": state.workflow_type,
                "failure_category": "validation",
                "error": str(error),
                "suggested_fix": (state.next_action or {}).get("reason"),
            })

    def _parameter_database(self, material_system: str | None) -> dict[str, Any]:
        card = self.parameter_store.resolve(material_system or "")
        if card is None:
            return {"status": "not_found", "material": material_system}
        payload = dict(card.parameters or {})
        return {
            "status": "loaded",
            "material_id": card.material_id,
            "material_name": card.material_name,
            "confidence": card.confidence,
            "cp_parameters": dict(payload.get("plastic") or {}),
            "elastic_constants": dict(payload.get("elastic") or {}),
            "is_demo_template": card.is_demo_template,
            "source_path": card.source_path,
        }

    def _literature_memory(self, material_system: str | None) -> list[dict[str, Any]]:
        card = self.parameter_store.resolve(material_system or "")
        if card is None:
            return []
        payload = dict(card.parameters or {})
        metadata = dict(payload.get("metadata") or {})
        return [{
            "material_id": card.material_id,
            "material_name": card.material_name,
            "sources": list(metadata.get("sources") or []),
            "confidence": card.confidence,
        }]

    def _workspace_simulation_records(self, material_system: str | None) -> list[dict[str, Any]]:
        if not self.workspace_root.exists():
            return []
        token = (material_system or "").lower()
        matches: list[dict[str, Any]] = []
        for state_path in sorted(self.workspace_root.glob("*/research_state.json")):
            try:
                payload = json.loads(state_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            selected_material = str(payload.get("selected_material_key") or "").lower()
            goal_material = str((payload.get("goal") or {}).get("material_system") or "").lower()
            if token and token not in {selected_material, goal_material}:
                continue
            matches.append({
                "workspace": state_path.parent.name,
                "state_path": str(state_path),
                "selected_material_key": payload.get("selected_material_key"),
                "goal": payload.get("goal"),
                "has_run_report": bool(payload.get("run_report")),
            })
        return matches[:10]

    @staticmethod
    def _to_jsonable(value: Any) -> dict[str, Any]:
        if value is None:
            return {}
        dumper = getattr(value, "model_dump", None)
        if dumper is not None:
            return dict(dumper())
        if isinstance(value, dict):
            return dict(value)
        if hasattr(value, "dict"):
            return dict(value.dict())
        return {"value": value}

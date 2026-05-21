"""Materials knowledge graph infrastructure for DAMASK Copilot."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from damask_copilot.memory.parameter_store import ParameterStore


class MaterialsKnowledgeGraph:
    """Small typed knowledge graph connecting materials, phases, models, and experiments."""

    def __init__(self, *, data_dir: Path | None = None, parameter_store: ParameterStore | None = None) -> None:
        self.data_dir = data_dir or Path("data/materials")
        self.parameter_store = parameter_store or ParameterStore(data_dir=self.data_dir)
        if not self.parameter_store.list_ids():
            self.parameter_store.load_library()
        self._graph = self._build_graph()

    def get_material_context(self, material_id: str | None) -> dict[str, Any]:
        token = material_id or ""
        card = self.parameter_store.resolve(token)
        if card is None:
            return {"material": None, "nodes": [], "edges": []}

        normalized_id = card.material_id
        nodes: list[dict[str, Any]] = []
        for node in self._graph["nodes"]:
            if node["id"] == f"material:{normalized_id}" or any(
                edge["source"] == f"material:{normalized_id}" and edge["target"] == node["id"] for edge in self._graph["edges"]
            ):
                nodes.append(dict(node))

        edges = [
            dict(edge)
            for edge in self._graph["edges"]
            if edge["source"] == f"material:{normalized_id}" or edge["target"] == f"material:{normalized_id}"
        ]
        return {
            "material": normalized_id,
            "nodes": nodes,
            "edges": edges,
        }

    def neighbors(self, node_id: str) -> list[dict[str, Any]]:
        linked_ids = [
            edge["target"] if edge["source"] == node_id else edge["source"]
            for edge in self._graph["edges"]
            if edge["source"] == node_id or edge["target"] == node_id
        ]
        return [dict(node) for node in self._graph["nodes"] if node["id"] in linked_ids]

    def export(self) -> dict[str, Any]:
        return {
            "nodes": [dict(node) for node in self._graph["nodes"]],
            "edges": [dict(edge) for edge in self._graph["edges"]],
        }

    def _build_graph(self) -> dict[str, list[dict[str, Any]]]:
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []
        index_path = self.data_dir / "index.yaml"
        index_payload = yaml.safe_load(index_path.read_text(encoding="utf-8")) if index_path.exists() else {}
        materials = dict((index_payload or {}).get("materials", {}))

        for material_id in self.parameter_store.list_ids():
            card = self.parameter_store.get(material_id)
            if card is None:
                continue

            material_node = {
                "id": f"material:{material_id}",
                "type": "material",
                "label": card.material_name,
                "attributes": {"aliases": list(materials.get(material_id, {}).get("aliases", []))},
            }
            nodes.append(material_node)

            phase_type = card.phase_type or "unknown_phase"
            phase_node_id = f"phase:{phase_type}"
            crystal_structure = card.crystal_structure or "unknown_structure"
            crystal_node_id = f"crystal_structure:{crystal_structure}"
            nodes.extend([
                {"id": phase_node_id, "type": "phase", "label": phase_type, "attributes": {}},
                {"id": crystal_node_id, "type": "crystal_structure", "label": crystal_structure, "attributes": {}},
            ])
            edges.extend([
                {"source": material_node["id"], "target": phase_node_id, "type": "has_phase"},
                {"source": material_node["id"], "target": crystal_node_id, "type": "has_crystal_structure"},
            ])

            payload = dict(card.parameters or {})
            paper_sources = list(self._paper_sources(payload))
            for source in paper_sources:
                paper_id = self._safe_node_id("literature", source)
                nodes.append({"id": paper_id, "type": "literature_paper", "label": source, "attributes": {}})
                edges.append({"source": material_node["id"], "target": paper_id, "type": "reported_in"})

            plastic = self._plastic_payload(payload)
            model_type = str(plastic.get("type") or "unknown_model")
            model_node_id = self._safe_node_id("damask_model", model_type)
            nodes.append({"id": model_node_id, "type": "damask_model", "label": model_type, "attributes": {}})
            edges.append({"source": material_node["id"], "target": model_node_id, "type": "uses_model"})
            edges.append({"source": model_node_id, "target": phase_node_id, "type": "valid_for_phase"})

            parameter_names = sorted(key for key in plastic.keys() if key != "type")
            for name in parameter_names:
                parameter_node_id = self._safe_node_id("cp_parameter", name)
                nodes.append({"id": parameter_node_id, "type": "cp_parameter", "label": name, "attributes": {"value": plastic.get(name)}})
                edges.extend([
                    {"source": material_node["id"], "target": parameter_node_id, "type": "has_cp_parameter"},
                    {"source": model_node_id, "target": parameter_node_id, "type": "requires_parameter"},
                ])

            for slip in self._slip_system_nodes(plastic):
                nodes.append(slip)
                edges.append({"source": material_node["id"], "target": slip["id"], "type": "has_slip_system"})

        return {
            "nodes": _dedupe_dicts(nodes, key="id"),
            "edges": _dedupe_edges(edges),
        }

    def _paper_sources(self, payload: dict[str, Any]) -> list[str]:
        metadata = dict(payload.get("metadata") or {})
        sources = list(metadata.get("sources") or [])
        return [str(item) for item in sources if item]

    def _plastic_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("plastic"):
            return dict(payload["plastic"])
        materialpoint = dict(payload.get("damask", {}).get("materialpoint", {}))
        phase_mapping = dict(materialpoint.get("phase", {}))
        phase_name = next(iter(phase_mapping.keys()), None)
        if phase_name is None:
            return {}
        return dict(phase_mapping.get(phase_name, {}).get("mechanical", {}).get("plastic", {}))

    def _slip_system_nodes(self, plastic: dict[str, Any]) -> list[dict[str, Any]]:
        slip_count = plastic.get("N_sl")
        if isinstance(slip_count, list):
            counts = [int(item) for item in slip_count if isinstance(item, (int, float))]
        elif isinstance(slip_count, (int, float)):
            counts = [int(slip_count)]
        else:
            counts = []
        nodes = []
        for index, count in enumerate(counts):
            label = f"slip_family_{index + 1}"
            nodes.append({
                "id": self._safe_node_id("slip_system", label),
                "type": "slip_system",
                "label": label,
                "attributes": {"count": count},
            })
        return nodes

    @staticmethod
    def _safe_node_id(prefix: str, raw: str) -> str:
        return f"{prefix}:{str(raw).strip().lower().replace(' ', '_')}"


def _dedupe_dicts(items: list[dict[str, Any]], *, key: str) -> list[dict[str, Any]]:
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for item in items:
        token = str(item.get(key))
        if token in seen:
            continue
        seen.add(token)
        deduped.append(item)
    return deduped


def _dedupe_edges(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[dict[str, Any]] = []
    for item in items:
        token = (str(item.get("source")), str(item.get("target")), str(item.get("type")))
        if token in seen:
            continue
        seen.add(token)
        deduped.append(item)
    return deduped

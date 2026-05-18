"""Local parameter store used as a stand-in material database."""

from __future__ import annotations

from pathlib import Path

import yaml

from damask_copilot.schemas.material import MaterialParameterCard


class ParameterStore:
    """Hybrid in-memory and file-backed store for material parameter cards."""

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or Path("data/materials")
        self._items: dict[str, MaterialParameterCard] = {}
        self._aliases: dict[str, str] = {}

    def load_library(self) -> None:
        """Load the local demo material library into the store."""
        index_path = self.data_dir / "index.yaml"
        with index_path.open("r", encoding="utf-8") as handle:
            index_data = yaml.safe_load(handle) or {}

        materials = index_data.get("materials", {})
        for material_id, entry in materials.items():
            material_path = self.data_dir / entry["file"]
            with material_path.open("r", encoding="utf-8") as handle:
                material_data = yaml.safe_load(handle) or {}
            card = MaterialParameterCard(
                material_id=material_id,
                material_name=material_data.get("material_name", material_id),
                crystal_structure=material_data.get("crystal_structure", "unknown"),
                phase_type=material_data.get("phase_type", "unknown"),
                source_path=str(material_path),
                confidence=material_data.get("metadata", {}).get("confidence", "medium"),
                explicit_assumptions=material_data.get("metadata", {}).get("explicit_assumptions", []),
                is_demo_template=bool(material_data.get("metadata", {}).get("is_demo_template", False)),
                parameters=material_data,
            )
            self.put(card)
            self._aliases[material_id.lower()] = material_id
            self._aliases[card.material_name.lower()] = material_id
            for alias in entry.get("aliases", []):
                self._aliases[alias.lower()] = material_id

    def put(self, card: MaterialParameterCard) -> None:
        self._items[card.material_id] = card

    def get(self, material_id: str) -> MaterialParameterCard | None:
        return self._items.get(material_id)

    def resolve(self, query: str) -> MaterialParameterCard | None:
        """Resolve a material by id, name, or configured alias."""
        material_id = self._aliases.get(query.lower(), query)
        return self._items.get(material_id)

    def list_ids(self) -> list[str]:
        return sorted(self._items)

"""Parameter memory store."""

from __future__ import annotations

from damask_copilot.schemas.material import MaterialParameterCard


class ParameterStore:
    """Minimal in-memory store for material parameter cards."""

    def __init__(self) -> None:
        self._items: dict[str, MaterialParameterCard] = {}

    def put(self, card: MaterialParameterCard) -> None:
        self._items[card.material_id] = card

    def get(self, material_id: str) -> MaterialParameterCard | None:
        return self._items.get(material_id)

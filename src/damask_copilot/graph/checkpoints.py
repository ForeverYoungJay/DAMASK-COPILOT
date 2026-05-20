"""Checkpoint helpers for LangGraph."""

from __future__ import annotations

import pickle
from collections import defaultdict
from pathlib import Path

from damask_copilot.schemas.checker_report import CheckerReport
from damask_copilot.schemas.critic_report import CriticReport
from damask_copilot.schemas.files import GeneratedFiles
from damask_copilot.schemas.llm_outputs import (
    IterationDecisionOutput,
    LiteratureAgentOutput,
    MaterialKnowledgeOutput,
    ReportWriterOutput,
    ResearchManagerOutput,
    ScientificCriticOutput,
    SimulationPlannerOutput,
)
from damask_copilot.schemas.material import MaterialParameterCard
from damask_copilot.schemas.postprocess_report import PostprocessReport
from damask_copilot.schemas.research_goal import ResearchGoal
from damask_copilot.schemas.run_report import RunReport
from damask_copilot.schemas.simulation_plan import GeometrySpec, LoadingSpec, SimulationPlan


ALLOWED_MSGPACK_TYPES = (
    ResearchGoal,
    ResearchManagerOutput,
    LiteratureAgentOutput,
    MaterialKnowledgeOutput,
    SimulationPlannerOutput,
    ScientificCriticOutput,
    ReportWriterOutput,
    MaterialParameterCard,
    GeometrySpec,
    LoadingSpec,
    SimulationPlan,
    GeneratedFiles,
    CheckerReport,
    RunReport,
    PostprocessReport,
    CriticReport,
    IterationDecisionOutput,
)


from langgraph.checkpoint.memory import InMemorySaver


class PersistentMemorySaver(InMemorySaver):
    """File-backed wrapper around LangGraph's in-memory saver."""

    def __init__(self, storage_path: str | Path, *, serde) -> None:
        self.storage_path = Path(storage_path)
        super().__init__(serde=serde)
        self._load()

    def _load(self) -> None:
        if not self.storage_path.exists():
            return
        with self.storage_path.open("rb") as handle:
            payload = pickle.load(handle)
        loaded_storage = payload.get("storage", {})
        storage = defaultdict(lambda: defaultdict(dict))
        for key, value in loaded_storage.items():
            inner = defaultdict(dict)
            inner.update(value)
            storage[key] = inner
        self.storage = storage
        self.writes = defaultdict(dict, payload.get("writes", {}))
        self.blobs = defaultdict(None, payload.get("blobs", {}))

    def persist(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "storage": _plain(self.storage),
            "writes": _plain(self.writes),
            "blobs": _plain(self.blobs),
        }
        with self.storage_path.open("wb") as handle:
            pickle.dump(payload, handle)


def build_checkpointer(enabled: bool = True, *, storage_path: str | Path | None = None):
    """Return a MemorySaver checkpointer when enabled."""
    if not enabled:
        return None
    from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

    serde = JsonPlusSerializer(allowed_msgpack_modules=ALLOWED_MSGPACK_TYPES)
    if storage_path is not None:
        return PersistentMemorySaver(storage_path=storage_path, serde=serde)
    from langgraph.checkpoint.memory import MemorySaver

    return MemorySaver(serde=serde)


def _plain(value):
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(_plain(item) for item in value)
    return value

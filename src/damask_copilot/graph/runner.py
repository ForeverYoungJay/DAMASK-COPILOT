"""Runtime helper for the primary LangGraph DAMASK research graph."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import yaml

from damask_copilot.graph.graph import build_damask_research_graph
from damask_copilot.graph.state import DamaskResearchState, create_initial_state
from damask_copilot.llm.structured_runner import StructuredLLMRunner


def run_research_graph(
    user_query: str,
    mode: str,
    use_llm: bool,
    model: str | None,
    max_iterations: int,
    *,
    approve: bool = False,
    allow_overwrite: bool = False,
    checkpoint: bool = True,
    thread_id: str | None = None,
    llm_runner: StructuredLLMRunner | None = None,
    agent_overrides: dict[str, Any] | None = None,
    stream: bool = True,
) -> DamaskResearchState:
    """Run the LangGraph research graph and return the final state."""
    query, resolved_mode, resolved_use_llm, resolved_model, resolved_max_iterations = _resolve_input(
        user_query=user_query,
        mode=mode,
        use_llm=use_llm,
        model=model,
        max_iterations=max_iterations,
    )
    initial_state = create_initial_state(
        user_query=query,
        mode=resolved_mode,
        use_llm=resolved_use_llm,
        model=resolved_model,
        max_iterations=resolved_max_iterations,
        explicit_approval=approve,
        allow_overwrite=allow_overwrite,
    )
    app = build_damask_research_graph(
        checkpoint=checkpoint,
        use_llm=resolved_use_llm,
        model=resolved_model,
        llm_runner=llm_runner,
        agent_overrides=agent_overrides,
    )
    config = {"configurable": {"thread_id": thread_id or f"damask-copilot-{uuid.uuid4()}"}}
    if stream:
        for update in app.stream(initial_state, config=config, stream_mode="updates"):
            for node_name, node_update in update.items():
                print(f"[{node_name}] updated: {_describe_node_update(node_update)}")
        snapshot = app.get_state(config)
        return snapshot.values
    return app.invoke(initial_state, config=config)


def _resolve_input(
    *,
    user_query: str,
    mode: str,
    use_llm: bool,
    model: str | None,
    max_iterations: int,
) -> tuple[str, str, bool, str | None, int]:
    input_path = Path(user_query)
    if input_path.exists() and input_path.suffix in {".yaml", ".yml"}:
        payload = yaml.safe_load(input_path.read_text(encoding="utf-8")) or {}
        return (
            payload.get("query", payload.get("user_query", "")),
            payload.get("mode", mode),
            bool(payload.get("use_llm", use_llm)),
            payload.get("model", model),
            int(payload.get("max_iterations", max_iterations)),
        )
    return user_query, mode, use_llm, model, max_iterations


def _describe_node_update(node_update: Any) -> str:
    """Return a safe, human-readable summary for streamed node updates."""
    if hasattr(node_update, "keys"):
        return str(sorted(node_update.keys()))
    if isinstance(node_update, (list, tuple)):
        return f"{type(node_update).__name__}(len={len(node_update)})"
    return type(node_update).__name__

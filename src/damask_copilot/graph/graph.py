"""LangGraph builder for DAMASK Copilot.

The primary graph now follows the v1 7-agent architecture.
"""

from __future__ import annotations

from damask_copilot.graph.checkpoints import build_checkpointer
from damask_copilot.graph.workflow import build_v1_graph
from damask_copilot.llm.structured_runner import StructuredLLMRunner


def build_damask_research_graph(
    checkpoint: bool = True,
    *,
    use_llm: bool = False,
    model: str | None = None,
    llm_runner: StructuredLLMRunner | None = None,
    agent_overrides: dict | None = None,
):
    """Build the primary LangGraph DAMASK research graph."""
    return build_v1_graph(
        checkpoint=checkpoint,
        use_llm=use_llm,
        model=model,
        llm_runner=llm_runner,
        agent_overrides=agent_overrides,
        checkpointer=build_checkpointer(checkpoint),
    )

"""Checkpoint helpers for LangGraph."""

from __future__ import annotations


def build_checkpointer(enabled: bool = True):
    """Return a MemorySaver checkpointer when enabled."""
    if not enabled:
        return None
    from langgraph.checkpoint.memory import MemorySaver

    return MemorySaver()

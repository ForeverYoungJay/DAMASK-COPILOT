"""Helpers for marking legacy micro-agents as compatibility wrappers."""

from __future__ import annotations

import warnings


def warn_legacy_agent(*, legacy_name: str, replacement: str) -> None:
    """Emit a deprecation warning for a legacy micro-agent."""
    warnings.warn(
        (
            f"{legacy_name} is deprecated and retained only as a compatibility wrapper. "
            f"Use {replacement} in the unified v1 DAMASK Copilot architecture."
        ),
        DeprecationWarning,
        stacklevel=3,
    )

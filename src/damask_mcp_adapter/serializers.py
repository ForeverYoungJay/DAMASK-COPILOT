"""JSON-safe serialization helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from damask_mcp_adapter.validators import ensure_workspace_write_path


def summarize_array(array: np.ndarray, *, max_preview: int = 5) -> dict[str, Any]:
    """Return a compact summary for a NumPy array."""
    arr = np.asarray(array)
    flat = arr.reshape(-1) if arr.size else arr
    preview = flat[:max_preview].tolist() if arr.size else []
    summary: dict[str, Any] = {
        "shape": list(arr.shape),
        "dtype": str(arr.dtype),
        "size": int(arr.size),
        "preview": preview,
    }
    if arr.size and np.issubdtype(arr.dtype, np.number):
        summary.update(
            {
                "min": float(np.min(arr)),
                "max": float(np.max(arr)),
                "mean": float(np.mean(arr)),
            }
        )
    return summary


def to_jsonable(value: Any) -> Any:
    """Convert values into JSON-serializable structures."""
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return summarize_array(value)
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, pd.DataFrame):
        return {
            "columns": list(value.columns),
            "rows": len(value),
            "preview": value.head(5).to_dict(orient="records"),
        }
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    return value


def write_dataframe_csv(dataframe: pd.DataFrame, output_csv: str | Path) -> Path:
    """Write a DataFrame as CSV under workspaces/."""
    output_path = ensure_workspace_write_path(output_csv)
    dataframe.to_csv(output_path, index=False)
    return output_path


def write_numpy_npy(array: np.ndarray, output_npy: str | Path) -> Path:
    """Write a NumPy array under workspaces/."""
    output_path = ensure_workspace_write_path(output_npy)
    np.save(output_path, array)
    return output_path

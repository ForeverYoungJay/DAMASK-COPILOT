"""Execution helpers with safe fallbacks when DAMASK is unavailable."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from damask_copilot.mcp_clients.damask_runner_client import DAMASKRunnerClient


def run_damask_grid(geometry_path: str, load_yaml_path: str, material_yaml_path: str, workdir: str) -> dict[str, Any]:
    """Run DAMASK_grid when available, otherwise return a structured fallback."""
    workdir_path = Path(workdir)
    workdir_path.mkdir(parents=True, exist_ok=True)
    log_path = workdir_path / "run.log"

    missing = [
        path
        for path in (geometry_path, load_yaml_path, material_yaml_path)
        if not Path(path).exists()
    ]
    if missing:
        message = f"Required DAMASK input files are missing: {missing}"
        log_path.write_text(message + "\n", encoding="utf-8")
        return {
            "ok": False,
            "status": "failed",
            "log_path": str(log_path),
            "error": message,
            "result_files": [],
            "detected_errors": detect_common_damask_errors(message),
            "failure_category": "input",
        }

    try:
        client = DAMASKRunnerClient()
        result = client.run(
            workspace=workdir_path.name,
            geometry=Path(geometry_path).name,
            load=Path(load_yaml_path).name,
            material=Path(material_yaml_path).name,
            numerics="numerics.yaml" if (workdir_path / "numerics.yaml").exists() else None,
            timeout_seconds=3600,
        )
        stdout_tail = "\n".join(result.get("stdout_tail", []))
        stderr_tail = "\n".join(result.get("stderr_tail", []))
        log_text = "\n".join(part for part in [stdout_tail, stderr_tail] if part).strip()
        if not log_text:
            log_text = result.get("error", "DAMASK run completed without log output.")
        log_path.write_text(log_text + "\n", encoding="utf-8")
        return {
            "ok": bool(result.get("ok", False)),
            "status": "success" if result.get("ok", False) else "failed",
            "returncode": result.get("returncode"),
            "log_path": str(log_path),
            "result_files": list(result.get("result_files", [])),
            "error": result.get("error"),
            "detected_errors": detect_common_damask_errors(log_text),
            "failure_category": classify_execution_failure(log_text, result.get("error")),
        }
    except Exception as exc:
        message = f"DAMASK execution is not available in this environment: {type(exc).__name__}: {exc}"
        log_path.write_text(message + "\n", encoding="utf-8")
        return {
            "ok": False,
            "status": "not_available",
            "log_path": str(log_path),
            "error": message,
            "result_files": [],
            "detected_errors": detect_common_damask_errors(message),
            "failure_category": "environment",
        }


def collect_result_files(workdir: str) -> dict[str, Any]:
    """Collect result files for a workspace using the runner MCP client."""
    workspace = Path(workdir).name
    try:
        client = DAMASKRunnerClient()
        result = client.collect_results(workspace=workspace)
        return {
            "ok": bool(result.get("ok", False)),
            "workspace": workspace,
            "result_files": list(result.get("files", [])),
            "count": int(result.get("count", len(result.get("files", [])))),
            "error": result.get("error"),
        }
    except Exception as exc:
        return {
            "ok": False,
            "workspace": workspace,
            "result_files": [],
            "count": 0,
            "error": f"{type(exc).__name__}: {exc}",
        }


def parse_damask_log(log_path: str) -> dict[str, Any]:
    """Parse a DAMASK log file into a structured summary."""
    path = Path(log_path)
    if not path.exists():
        return {"ok": False, "errors": [f"Log file does not exist: {log_path}"]}
    text = path.read_text(encoding="utf-8", errors="ignore")
    return {
        "ok": True,
        "log_path": str(path),
        "line_count": len(text.splitlines()),
        "detected_errors": detect_common_damask_errors(text),
    }


def detect_common_damask_errors(log_text: str) -> dict[str, Any]:
    """Detect common DAMASK errors from raw log text."""
    lowered = log_text.lower()
    matched: list[str] = []
    if "material index out of bounds" in lowered:
        matched.append("material_index_out_of_bounds")
    if "more materials requested than found in material.yaml" in lowered:
        matched.append("material_count_mismatch")
    if "segmentation fault" in lowered:
        matched.append("segmentation_fault")
    if "timeout" in lowered:
        matched.append("timeout")
    if "no such file" in lowered or "not found" in lowered:
        matched.append("missing_file_or_executable")
    return {"matched_errors": matched, "has_errors": bool(matched)}


def classify_execution_failure(log_text: str | None, error_text: str | None = None) -> str | None:
    """Classify DAMASK execution failures into broad categories."""
    text = " ".join(part for part in [log_text or "", error_text or ""] if part).lower()
    if not text:
        return None
    if "material index out of bounds" in text or "more materials requested" in text:
        return "input"
    if "no such file" in text or "not found" in text:
        return "environment"
    if "timeout" in text:
        return "environment"
    if "segmentation fault" in text:
        return "solver"
    if "plastic" in text or "constitutive" in text or "phase" in text:
        return "model"
    return "execution"

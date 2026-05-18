"""Core DAMASK inspection and environment helpers."""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path
from typing import Any

from damask_mcp_adapter.workspace import damask_python_root, import_damask


def _safe_signature(obj: Any) -> str | None:
    try:
        return str(inspect.signature(obj))
    except Exception:
        return None


def _safe_doc(obj: Any) -> str | None:
    doc = inspect.getdoc(obj)
    if doc is None:
        return None
    lines = [line.rstrip() for line in doc.splitlines()[:20]]
    return "\n".join(lines)


def check_damask_installation() -> dict[str, Any]:
    """Check whether the local DAMASK Python package can be imported."""
    try:
        damask = import_damask()
        return {
            "ok": True,
            "imported": True,
            "version": getattr(damask, "__version__", None),
            "source_root": str(damask_python_root().resolve()),
            "module_file": str(Path(damask.__file__).resolve()),
        }
    except Exception as exc:
        return {
            "ok": False,
            "imported": False,
            "source_root": str(damask_python_root().resolve()),
            "error": f"{type(exc).__name__}: {exc}",
        }


def get_damask_version() -> dict[str, Any]:
    """Return the local DAMASK Python package version."""
    result = check_damask_installation()
    if not result["ok"]:
        return result
    return {
        "ok": True,
        "version": result["version"],
        "module_file": result["module_file"],
    }


def list_damask_modules() -> dict[str, Any]:
    """List the main modules and classes exported by DAMASK."""
    try:
        damask = import_damask()
        exported = sorted(name for name in dir(damask) if not name.startswith("_"))
        return {
            "ok": True,
            "count": len(exported),
            "exports": exported,
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def inspect_damask_class(class_name: str) -> dict[str, Any]:
    """Inspect a DAMASK class exported from the top-level package."""
    try:
        damask = import_damask()
        obj = getattr(damask, class_name)
        if not inspect.isclass(obj):
            return {"ok": False, "class_name": class_name, "error": f"{class_name} is not a class."}
        methods = []
        for name, member in inspect.getmembers(obj):
            if name.startswith("_"):
                continue
            if callable(member):
                methods.append({"name": name, "signature": _safe_signature(member)})
        return {
            "ok": True,
            "class_name": class_name,
            "module": getattr(obj, "__module__", None),
            "doc": _safe_doc(obj),
            "method_count": len(methods),
            "methods": methods[:200],
            "truncated": len(methods) > 200,
        }
    except Exception as exc:
        return {"ok": False, "class_name": class_name, "error": f"{type(exc).__name__}: {exc}"}


def inspect_damask_function(function_name: str) -> dict[str, Any]:
    """Inspect a DAMASK function from the top-level package or main submodules."""
    module_candidates = [
        "damask",
        "damask.mechanics",
        "damask.tensor",
        "damask.util",
        "damask.grid_filters",
        "damask.seeds",
    ]
    for module_name in module_candidates:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, function_name):
                obj = getattr(module, function_name)
                if not callable(obj):
                    return {
                        "ok": False,
                        "function_name": function_name,
                        "module": module_name,
                        "error": f"{function_name} exists in {module_name} but is not callable.",
                    }
                return {
                    "ok": True,
                    "function_name": function_name,
                    "module": module_name,
                    "signature": _safe_signature(obj),
                    "doc": _safe_doc(obj),
                }
        except Exception:
            continue
    return {"ok": False, "function_name": function_name, "error": f"Function not found: {function_name}"}


__all__ = [
    "check_damask_installation",
    "get_damask_version",
    "inspect_damask_class",
    "inspect_damask_function",
    "list_damask_modules",
]

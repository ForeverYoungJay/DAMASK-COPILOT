from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from damask_copilot.graph.graph import build_damask_research_graph
from damask_copilot.graph.materials_research_graph import build_materials_research_graph
from damask_copilot.graph.workflow import build_v1_graph


def main() -> None:
    out_dir = REPO_ROOT / "workspaces" / "graph_diagrams"
    out_dir.mkdir(parents=True, exist_ok=True)

    graphs = {
        "v1_workflow": build_v1_graph(checkpoint=False),
        "primary_graph_alias": build_damask_research_graph(checkpoint=False),
        "materials_graph_alias": build_materials_research_graph(checkpoint=False),
    }

    saved_paths: list[Path] = []
    for name, app in graphs.items():
        saved_paths.extend(_write_graph_artifacts(name=name, app=app, out_dir=out_dir))

    print("Current DAMASK Copilot graph artifacts:")
    for path in saved_paths:
        print(path.resolve())
    print()
    print("Notes:")
    print("- `v1_workflow` is the current 7-agent architecture.")
    print("- `primary_graph_alias` and `materials_graph_alias` are compatibility entry points that both compile to the v1 graph.")


def _write_graph_artifacts(*, name: str, app, out_dir: Path) -> list[Path]:
    graph = app.get_graph()
    written: list[Path] = []

    mermaid_text = _draw_mermaid_text(graph)
    if mermaid_text is not None:
        mermaid_path = out_dir / f"{name}.mmd"
        mermaid_path.write_text(mermaid_text, encoding="utf-8")
        written.append(mermaid_path)

    mermaid_png = _draw_mermaid_png(graph)
    if mermaid_png is not None:
        png_path = out_dir / f"{name}.png"
        png_path.write_bytes(mermaid_png)
        written.append(png_path)

    return written


def _draw_mermaid_text(graph) -> str | None:
    for attr in ("draw_mermaid",):
        drawer = getattr(graph, attr, None)
        if callable(drawer):
            return drawer()
    return None


def _draw_mermaid_png(graph) -> bytes | None:
    for attr in ("draw_mermaid_png",):
        drawer = getattr(graph, attr, None)
        if callable(drawer):
            try:
                return drawer()
            except Exception as exc:
                print(f"Skipping PNG render for current graph because Mermaid PNG rendering failed: {type(exc).__name__}: {exc}")
                return None
    return None


if __name__ == "__main__":
    main()

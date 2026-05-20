from pathlib import Path
from damask_copilot.graph.graph import build_damask_research_graph
from damask_copilot.graph.materials_research_graph import build_materials_research_graph

old_chain = build_damask_research_graph(checkpoint=False)
new_chain = build_materials_research_graph(checkpoint=False)

out_dir = Path("workspaces/graph_diagrams")
out_dir.mkdir(parents=True, exist_ok=True)

old_png = old_chain.get_graph().draw_mermaid_png()
new_png = new_chain.get_graph().draw_mermaid_png()

(old_dir := out_dir / "damask_research_graph.png").write_bytes(old_png)
(new_dir := out_dir / "materials_research_graph.png").write_bytes(new_png)

print(old_dir.resolve())
print(new_dir.resolve())
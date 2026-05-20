from damask_copilot.graph import materials_research_graph


class _FakeSnapshot:
    def __init__(self):
        self.values = {"report_path": "workspaces/materials_report.md"}


class _FakeApp:
    def stream(self, initial_state, config=None, stream_mode=None):
        yield {"research_manager": {"research_case": {"material_system": "fcc_al"}}}
        yield {"human_review_framing": ("interrupt", {"stage": "human_review_framing"})}

    def get_state(self, config=None):
        return _FakeSnapshot()


def test_run_materials_research_graph_stream_handles_tuple_updates(monkeypatch, capsys):
    monkeypatch.setattr(materials_research_graph, "build_materials_research_graph", lambda **kwargs: _FakeApp())

    final_state = materials_research_graph.run_materials_research_graph(
        "Study FCC aluminum under uniaxial tension",
        mode="dry_run",
        use_llm=False,
        checkpoint=False,
        stream=True,
    )

    assert final_state["report_path"] == "workspaces/materials_report.md"
    output = capsys.readouterr().out
    assert "[research_manager] research case ready:" in output
    assert "[human_review_framing] updated (tuple, len=2)" in output

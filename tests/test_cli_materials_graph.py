import pytest

from damask_copilot import cli
from damask_copilot.graph.materials_research_graph import _resolve_materials_input


def test_cli_materials_run_invokes_materials_graph(monkeypatch, capsys):
    captured = {}

    def fake_run_materials_research_graph(**kwargs):
        captured.update(kwargs)
        return {"report_path": "workspaces/materials_report.md"}

    monkeypatch.setattr(cli, "run_materials_research_graph", fake_run_materials_research_graph)
    monkeypatch.setattr(
        "sys.argv",
        [
            "damask-copilot",
            "materials",
            "run",
            "Study FCC aluminum under uniaxial tension",
            "--dry-run",
            "--user-file",
            "notes.txt",
            "--literature-file",
            "data/literature/fcc_al/notes/project_notes.md",
            "--experimental-file",
            "exp.csv",
            "--source-list-file",
            "data/literature/fcc_al/source_lists/seed_sources.txt",
            "--literature-source",
            "doi:10.1000/example",
        ],
    )

    assert cli.main() == 0
    assert captured["user_query"] == "Study FCC aluminum under uniaxial tension"
    assert captured["mode"] == "dry_run"
    assert captured["user_files"] == ["notes.txt"]
    assert captured["literature_files"] == ["data/literature/fcc_al/notes/project_notes.md"]
    assert captured["experimental_files"] == ["exp.csv"]
    assert captured["literature_sources"] == ["doi:10.1000/example"]
    assert captured["source_list_files"] == ["data/literature/fcc_al/source_lists/seed_sources.txt"]
    output = capsys.readouterr().out
    assert "Completed materials research pipeline" in output


def test_cli_materials_run_prints_interrupt(monkeypatch, capsys):
    def fake_run_materials_research_graph(**kwargs):
        class _Interrupt:
            def __init__(self):
                self.value = {
                    "stage": "human_review_framing",
                    "review_type": "steering",
                    "research_case": {"material_system": "fcc_al"},
                }

        return {"__interrupt__": [_Interrupt()]}

    monkeypatch.setattr(cli, "run_materials_research_graph", fake_run_materials_research_graph)
    monkeypatch.setattr(
        "sys.argv",
        [
            "damask-copilot",
            "materials",
            "run",
            "Study FCC aluminum under uniaxial tension",
            "--dry-run",
            "--thread-id",
            "materials-thread-1",
        ],
    )

    assert cli.main() == 0
    output = capsys.readouterr().out
    assert "paused for human review" in output
    assert "materials-thread-1" in output
    assert "stage=human_review_framing" in output


def test_cli_materials_resume_invokes_resume_graph(monkeypatch, capsys):
    captured = {}

    def fake_resume_materials_research_graph(**kwargs):
        captured.update(kwargs)
        return {"report_path": "workspaces/materials_report.md", "__thread_id__": kwargs["thread_id"]}

    monkeypatch.setattr(cli, "resume_materials_research_graph", fake_resume_materials_research_graph)
    monkeypatch.setattr(
        "sys.argv",
        [
            "damask-copilot",
            "materials",
            "resume",
            "--thread-id",
            "materials-thread-2",
            "--decision",
            "approve",
            "--comments",
            "Proceed.",
            "--state-patch",
            '{"user_constraints":{"allow_overwrite":true}}',
        ],
    )

    assert cli.main() == 0
    assert captured["thread_id"] == "materials-thread-2"
    assert captured["decision"] == "approve"
    assert captured["comments"] == "Proceed."
    assert captured["state_patch"] == {"user_constraints": {"allow_overwrite": True}}
    output = capsys.readouterr().out
    assert "Resumed materials research pipeline" in output


def test_cli_materials_rejects_approve_without_full_run():
    parser = cli.build_parser()
    args = parser.parse_args(["materials", "run", "Study FCC aluminum under uniaxial tension", "--approve"])

    with pytest.raises(SystemExit):
        if args.approve and not args.allow_full_run:
            parser.error("--approve can only be used together with --full-run.")


def test_resolve_materials_input_expands_source_list_file(tmp_path):
    source_list = tmp_path / "sources.txt"
    source_list.write_text("# comments\ndoi:10.1000/example\narXiv:1234.56789\n", encoding="utf-8")

    payload = _resolve_materials_input(
        user_query="Study FCC aluminum under uniaxial tension",
        mode="dry_run",
        use_llm=False,
        model=None,
        max_iterations=1,
        literature_sources=["doi:10.1000/example"],
        source_list_files=[str(source_list)],
    )

    assert payload["literature_sources"] == ["doi:10.1000/example", "arXiv:1234.56789"]

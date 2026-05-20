from damask_copilot.agents.literature_agent import LiteratureAgent
from damask_copilot.mcp_clients.literature_mcp_client import LiteratureMCPClient
from damask_copilot.graph.materials_research_nodes import build_materials_research_nodes


class _MockLiteratureClient:
    def collect_literature(self, *, user_query: str, literature_sources: list):
        return {
            "used_external_retrieval": True,
            "providers_attempted": ["semantic_scholar", "arxiv"],
            "providers_succeeded": ["semantic_scholar"],
            "notes": [
                "Slip-controlled plasticity was reported for FCC aluminum.",
                "Stress-strain response was compared under uniaxial tension.",
            ],
            "summary": "External literature retrieval used 1 provider.",
            "evidence_items": [
                {
                    "provider": "semantic_scholar",
                    "tool": "get_paper_details",
                    "resolved_source": "DOI:10.1000/example",
                    "text": "Slip-controlled plasticity was reported for FCC aluminum under tension.",
                }
            ],
            "resolved_sources": ["DOI:10.1000/example"],
            "uncertainties": [],
        }


def test_literature_agent_uses_external_mcp_client():
    agent = LiteratureAgent(use_llm=False, literature_client=_MockLiteratureClient())
    state = {
        "user_query": "Study FCC aluminum under uniaxial tension",
        "mode": "dry_run",
        "use_llm": False,
        "model": None,
        "literature_sources": ["doi:10.1000/example"],
        "literature_notes": [],
        "trace": [],
        "errors": [],
    }

    updated = agent.run(state)

    assert "literature_external_results" in updated
    assert updated["literature_external_results"]["providers_succeeded"] == ["semantic_scholar"]
    assert any("Slip-controlled plasticity" in note for note in updated["literature_notes"])
    assert "literature_analysis" in updated
    assert "stress_strain_curve" in updated["literature_analysis"]["observables_for_validation"]


def test_materials_literature_node_compiles_external_results():
    nodes = build_materials_research_nodes(
        use_llm=False,
        agent_overrides={
            "literature_agent": LiteratureAgent(use_llm=False, literature_client=_MockLiteratureClient()),
        },
    )
    state = {
        "user_query": "Study FCC aluminum under uniaxial tension",
        "mode": "dry_run",
        "use_llm": False,
        "model": None,
        "literature_sources": ["doi:10.1000/example"],
        "trace": [],
        "errors": [],
        "research_case": {
            "material_system": "fcc_al",
            "objective": "Study response under uniaxial tension",
        },
    }

    updated = nodes["literature_agent"](state)

    review = updated["literature_review"]
    assert review["status"] == "literature_review_ready"
    assert "DOI:10.1000/example" in review["sources"]
    assert "stress_strain_curve" in review["observables_for_validation"]
    assert review["provider_summary"]["providers_succeeded"] == ["semantic_scholar"]
    assert review["planning_implications"]


def test_materials_literature_node_normalizes_sources_and_drops_query_noise():
    class _NoisyClient:
        def collect_literature(self, *, user_query: str, literature_sources: list):
            return {
                "used_external_retrieval": True,
                "providers_attempted": ["semantic_scholar", "elsevier", "arxiv"],
                "providers_succeeded": ["semantic_scholar", "arxiv"],
                "notes": ["Stress-strain response and texture evolution were discussed."],
                "summary": "Used two providers.",
                "evidence_items": [],
                "resolved_sources": [
                    "10.1000/example",
                    "DOI:10.1000/example",
                    "arXiv:1706.03762",
                    "1706.03762",
                    user_query,
                ],
                "uncertainties": [],
            }

    nodes = build_materials_research_nodes(
        use_llm=False,
        agent_overrides={
            "literature_agent": LiteratureAgent(use_llm=False, literature_client=_NoisyClient()),
        },
    )
    state = {
        "user_query": "Study FCC aluminum under uniaxial tension",
        "mode": "dry_run",
        "use_llm": False,
        "model": None,
        "literature_sources": ["doi:10.1000/example", "Study FCC aluminum under uniaxial tension"],
        "trace": [],
        "errors": [],
        "research_case": {"material_system": "fcc_al", "objective": "Study response under uniaxial tension"},
    }

    updated = nodes["literature_agent"](state)
    assert updated["literature_review"]["sources"] == ["DOI:10.1000/example", "ARXIV:1706.03762"]


def test_literature_agent_can_auto_search_without_user_sources():
    class _AutoSearchClient:
        def collect_literature(self, *, user_query: str, literature_sources: list):
            assert literature_sources == []
            return {
                "used_external_retrieval": True,
                "providers_attempted": ["semantic_scholar", "arxiv"],
                "providers_succeeded": ["semantic_scholar", "arxiv"],
                "notes": [
                    "A related FCC aluminum paper reported slip-dominated plasticity under tension.",
                    "A related arXiv preprint discussed orientation-sensitive stress-strain response.",
                ],
                "summary": "External literature retrieval used 2 providers.",
                "evidence_items": [
                    {
                        "provider": "semantic_scholar",
                        "tool": "search_papers",
                        "resolved_source": "Study FCC aluminum under uniaxial tension",
                        "text": "A related FCC aluminum paper reported slip-dominated plasticity under tension.",
                    },
                    {
                        "provider": "arxiv",
                        "tool": "read_paper",
                        "resolved_source": "1706.03762",
                        "text": "A related arXiv preprint discussed orientation-sensitive stress-strain response.",
                    },
                ],
                "resolved_sources": ["Study FCC aluminum under uniaxial tension", "1706.03762"],
                "uncertainties": [],
            }

    agent = LiteratureAgent(use_llm=False, literature_client=_AutoSearchClient())
    state = {
        "user_query": "Study FCC aluminum under uniaxial tension",
        "mode": "dry_run",
        "use_llm": False,
        "model": None,
        "literature_sources": [],
        "literature_notes": [],
        "trace": [],
        "errors": [],
    }

    updated = agent.run(state)
    assert updated["literature_external_results"]["providers_succeeded"] == ["semantic_scholar", "arxiv"]
    assert any("slip-dominated plasticity" in note for note in updated["literature_notes"])


def test_literature_client_defaults_to_auto_search_enabled():
    client = LiteratureMCPClient(providers=[], max_results=1, auto_search=None)
    assert client.auto_search is True


def test_literature_agent_reads_local_literature_files(tmp_path):
    note_path = tmp_path / "reading_notes.md"
    note_path.write_text(
        "# Notes\nNi3Al cold rolling may involve texture evolution and anisotropy.\n",
        encoding="utf-8",
    )

    class _SilentClient:
        def collect_literature(self, *, user_query: str, literature_sources: list):
            return {
                "used_external_retrieval": False,
                "providers_attempted": [],
                "providers_succeeded": [],
                "notes": [],
                "summary": "No external sources were supplied.",
                "evidence_items": [],
                "resolved_sources": [],
                "uncertainties": [],
            }

    agent = LiteratureAgent(use_llm=False, literature_client=_SilentClient())
    state = {
        "user_query": "Study Ni3Al cold rolling anisotropy",
        "mode": "dry_run",
        "use_llm": False,
        "model": None,
        "literature_files": [str(note_path)],
        "literature_sources": [],
        "literature_notes": [],
        "trace": [],
        "errors": [],
    }

    updated = agent.run(state)
    assert updated["literature_external_results"]["used_local_files"] is True
    assert any("reading_notes.md" in note for note in updated["literature_notes"])


def test_literature_agent_reads_local_file_sources_and_archives_retrieval(tmp_path):
    note_path = tmp_path / "source_notes.md"
    note_path.write_text(
        "# Imported source\nNi3Al cold rolling shows orientation-sensitive anisotropy.\n",
        encoding="utf-8",
    )

    workspace = tmp_path / "workspace_case"

    class _RetrievalClient:
        def collect_literature(self, *, user_query: str, literature_sources: list):
            return {
                "used_external_retrieval": True,
                "providers_attempted": ["semantic_scholar"],
                "providers_succeeded": ["semantic_scholar"],
                "notes": ["Retrieved article text discusses slip transfer and texture evolution."],
                "summary": "Retrieved 1 related article.",
                "evidence_items": [
                    {
                        "provider": "semantic_scholar",
                        "tool": "search_papers",
                        "resolved_source": "DOI:10.1000/retrieved",
                        "text": "Full retrieved article text about Ni3Al cold rolling texture evolution.",
                    }
                ],
                "resolved_sources": ["DOI:10.1000/retrieved"],
                "uncertainties": [],
            }

    agent = LiteratureAgent(use_llm=False, literature_client=_RetrievalClient())
    state = {
        "user_query": "Study Ni3Al cold rolling anisotropy",
        "mode": "dry_run",
        "use_llm": False,
        "model": None,
        "workspace": str(workspace),
        "literature_files": [],
        "literature_sources": [str(note_path)],
        "literature_notes": [],
        "trace": [],
        "errors": [],
    }

    updated = agent.run(state)

    local_files = updated["literature_external_results"]["local_files"]
    assert any(path.endswith("source_notes.md") for path in local_files)
    assert any(path.endswith(".md") and "semantic_scholar" in path for path in local_files)
    archive_dir = workspace / "literature"
    archived_files = list(archive_dir.glob("*.md"))
    assert archived_files
    assert "Full retrieved article text" in archived_files[0].read_text(encoding="utf-8")
    assert any("source_notes.md" in note for note in updated["literature_notes"])


def test_literature_agent_searches_first_then_reads_user_sources(tmp_path):
    note_path = tmp_path / "paper_notes.txt"
    note_path.write_text("User PDF notes mention Ni3Al cold rolling texture evolution.", encoding="utf-8")
    call_order = []

    class _OrderedClient:
        def search_related_literature(self, *, user_query: str):
            call_order.append(("search", user_query))
            return {
                "used_external_retrieval": True,
                "providers_attempted": ["semantic_scholar"],
                "providers_succeeded": ["semantic_scholar"],
                "notes": ["MCP search found a related Ni3Al cold-rolling article."],
                "summary": "Automatic MCP literature search used semantic_scholar.",
                "evidence_items": [
                    {
                        "provider": "semantic_scholar",
                        "tool": "search_papers",
                        "resolved_source": "DOI:10.1000/search-result",
                        "text": "A search result discusses Ni3Al cold rolling texture evolution.",
                    }
                ],
                "resolved_sources": ["DOI:10.1000/search-result"],
                "uncertainties": [],
            }

        def collect_from_sources(self, *, user_query: str, literature_sources: list):
            call_order.append(("sources", list(literature_sources)))
            return {
                "used_external_retrieval": True,
                "providers_attempted": ["elsevier"],
                "providers_succeeded": ["elsevier"],
                "notes": ["User DOI retrieval returned a focused article abstract."],
                "summary": "User-supplied literature retrieval used elsevier.",
                "evidence_items": [
                    {
                        "provider": "elsevier",
                        "tool": "abstract_retrieval",
                        "resolved_source": "DOI:10.1000/user-source",
                        "text": "The supplied DOI discusses ordered intermetallic rolling behavior.",
                    }
                ],
                "resolved_sources": ["DOI:10.1000/user-source"],
                "uncertainties": [],
            }

    agent = LiteratureAgent(use_llm=False, literature_client=_OrderedClient())
    state = {
        "user_query": "Study Ni3Al cold rolling anisotropy",
        "mode": "dry_run",
        "use_llm": False,
        "model": None,
        "literature_files": [str(note_path)],
        "literature_sources": ["doi:10.1000/user-source"],
        "literature_notes": [],
        "trace": [],
        "errors": [],
    }

    updated = agent.run(state)

    assert call_order == [
        ("search", "Study Ni3Al cold rolling anisotropy"),
        ("sources", ["doi:10.1000/user-source"]),
    ]
    assert updated["literature_external_results"]["providers_succeeded"] == ["semantic_scholar", "elsevier"]
    assert [item["stage"] for item in updated["literature_external_results"]["retrieval_stages"]] == [
        "auto_search",
        "user_sources",
    ]
    assert updated["literature_external_results"]["used_local_files"] is True
    assert "DOI:10.1000/search-result" in updated["literature_external_results"]["resolved_sources"]
    assert "DOI:10.1000/user-source" in updated["literature_external_results"]["resolved_sources"]
    assert any("paper_notes.txt" in path for path in updated["literature_external_results"]["local_files"])

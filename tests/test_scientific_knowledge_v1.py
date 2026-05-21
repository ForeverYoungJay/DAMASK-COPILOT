import pytest

from damask_copilot.agents.scientific_knowledge import ScientificKnowledgeAgent
from damask_copilot.graph.state import ResearchState


@pytest.fixture
def disabled_literature_client():
    class _DisabledLiteratureClient:
        def search_related_literature(self, *, user_query):
            return {
                "used_external_retrieval": False,
                "providers_attempted": [],
                "providers_succeeded": [],
                "notes": [],
                "summary": "Automatic literature search is disabled.",
                "evidence_items": [],
                "resolved_sources": [],
                "uncertainties": [],
            }

        def collect_literature(self, *, user_query, literature_sources):
            return self.search_related_literature(user_query=user_query)

    return _DisabledLiteratureClient()


def test_scientific_knowledge_agent_loads_material_and_history_knowledge(disabled_literature_client):
    state = ResearchState(
        user_goal="Calibrate a DAMASK crystal plasticity model for Ni3Al using tensile stress-strain data.",
        workflow_type="calibration",
        material_system="ni3al_l12",
        needs_literature=True,
        needs_experimental_data=False,
        use_llm=False,
    )

    updated = ScientificKnowledgeAgent(use_llm=False, literature_client=disabled_literature_client).run(state)

    assert updated.known_parameters is not None
    assert updated.known_parameters["status"] == "loaded"
    assert updated.known_parameters["elastic_constants"]["C_11"] > 0
    assert updated.known_parameters["reported_cp_parameters"]["type"] == "phenopowerlaw"
    assert updated.known_parameters["phase_information"]["phase_name"] == "Ni3Al"
    assert updated.known_parameters["materials_knowledge_graph_hits"]
    assert updated.known_parameters["scientific_memory_context"]["materials_knowledge_graph"]["material"] == "ni3al_l12"
    assert updated.damask_capabilities is not None
    assert updated.damask_capabilities["documentation_sources"]
    assert "previous_simulation_records" in updated.damask_capabilities
    assert updated.damask_capabilities["shared_memory_layer"]["cp_parameter_database"]["material_id"] == "ni3al_l12"


def test_scientific_knowledge_agent_skips_literature_when_not_needed(tmp_path, disabled_literature_client):
    state = ResearchState(
        user_goal="Generate DAMASK input files for Ni3Al.",
        workflow_type="damask_input_generation",
        material_system="ni3al_l12",
        needs_literature=False,
        needs_experimental_data=False,
        use_llm=False,
    )

    updated = ScientificKnowledgeAgent(
        use_llm=False,
        literature_client=disabled_literature_client,
        projects_root=tmp_path / "projects",
    ).run(state)

    assert updated.literature_summary is not None
    assert updated.literature_summary["status"] == "skipped"
    assert updated.experimental_data is not None
    assert updated.experimental_data["status"] == "skipped"


def test_scientific_knowledge_agent_directly_uses_literature_mcp_client():
    class _FakeLiteratureClient:
        def search_related_literature(self, *, user_query):
            assert "Ni3Al" in user_query
            return {
                "used_external_retrieval": True,
                "providers_attempted": ["semantic_scholar", "elsevier", "arxiv"],
                "providers_succeeded": ["semantic_scholar"],
                "notes": ["Ni3Al slip and tensile stress-strain behavior were discussed."],
                "summary": "External literature retrieval used 1 provider.",
                "evidence_items": [{"provider": "semantic_scholar", "text": "Ni3Al slip and tensile stress-strain behavior were discussed."}],
                "resolved_sources": ["doi:10.1000/example"],
                "uncertainties": [],
            }

    state = ResearchState(
        user_goal="Calibrate Ni3Al using tensile stress-strain data.",
        workflow_type="calibration",
        material_system="ni3al_l12",
        needs_literature=True,
        use_llm=False,
    )

    updated = ScientificKnowledgeAgent(use_llm=False, literature_client=_FakeLiteratureClient()).run(state)

    assert updated.literature_summary["status"] == "collected"
    assert updated.literature_summary["providers_succeeded"] == ["semantic_scholar"]
    assert "stress_strain_curve" in updated.literature_summary["observables_for_validation"]
    assert "planning_evidence" in updated.literature_summary
    assert "stress_strain_curve" in updated.literature_summary["planning_evidence"]["observables_for_validation"]
    assert updated.literature_summary["parameter_evidence"]["supports_parameter_lookup"] is True


def test_scientific_knowledge_agent_directly_reads_experimental_csv(tmp_path, disabled_literature_client):
    csv_path = tmp_path / "exp.csv"
    csv_path.write_text("strain,stress\n0.0,0.0\n0.01,100.0\n", encoding="utf-8")

    state = ResearchState(
        user_goal="Compare simulation and experiment for Ni3Al.",
        workflow_type="experiment_simulation_comparison",
        material_system="ni3al_l12",
        needs_experimental_data=True,
        experimental_files=[str(csv_path)],
        use_llm=False,
    )

    updated = ScientificKnowledgeAgent(use_llm=False, literature_client=disabled_literature_client).run(state)

    assert updated.experimental_data["status"] == "experimental_data_loaded"
    assert updated.experimental_data["curve"] == {"strain": [0.0, 0.01], "stress": [0.0, 100.0]}
    assert "stress" in updated.experimental_data["observable_candidates"]


def test_scientific_knowledge_agent_discovers_project_folder_contents(tmp_path, disabled_literature_client):
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "literature_note.md").write_text("Ni3Al crystal plasticity literature note", encoding="utf-8")
    (project_dir / "stress_strain.csv").write_text("strain,stress\n0.0,0.0\n0.01,100.0\n", encoding="utf-8")
    (project_dir / "source_list.txt").write_text("doi:10.1000/example\n", encoding="utf-8")

    class _ProjectLiteratureClient:
        def collect_literature(self, *, user_query, literature_sources):
            assert "doi:10.1000/example" in literature_sources
            return {
                "used_external_retrieval": True,
                "providers_attempted": ["semantic_scholar"],
                "providers_succeeded": ["semantic_scholar"],
                "notes": ["Ni3Al slip and stress-strain data were discussed."],
                "summary": "External literature retrieval used 1 provider.",
                "evidence_items": [],
                "resolved_sources": list(literature_sources),
                "uncertainties": [],
            }

    state = ResearchState(
        user_goal="Calibrate Ni3Al using tensile stress-strain data.",
        workflow_type="calibration",
        material_system="ni3al_l12",
        needs_literature=True,
        needs_experimental_data=True,
        project_dir=str(project_dir),
        use_llm=False,
    )

    updated = ScientificKnowledgeAgent(
        use_llm=False,
        literature_client=_ProjectLiteratureClient(),
    ).run(state)

    assert any(path.endswith("literature_note.md") for path in updated.literature_files)
    assert any(path.endswith("stress_strain.csv") for path in updated.experimental_files)
    assert "doi:10.1000/example" in updated.literature_sources
    assert updated.experimental_data["status"] == "experimental_data_loaded"


def test_scientific_knowledge_agent_adds_local_file_insights(tmp_path, disabled_literature_client):
    project_dir = tmp_path / "project"
    (project_dir / "literature" / "notes").mkdir(parents=True, exist_ok=True)
    (project_dir / "literature" / "pdf").mkdir(parents=True, exist_ok=True)
    (project_dir / "literature" / "source_lists").mkdir(parents=True, exist_ok=True)
    (project_dir / "literature" / "notes" / "reading_notes.md").write_text("Ni3Al slip and hardening note", encoding="utf-8")
    (project_dir / "literature" / "source_lists" / "seed_sources.txt").write_text("doi:10.1000/example\n", encoding="utf-8")
    (project_dir / "literature" / "pdf" / "paper.pdf").write_bytes(b"%PDF-1.4")

    state = ResearchState(
        user_goal="Plan a Ni3Al calibration study.",
        workflow_type="calibration",
        material_system="ni3al_l12",
        needs_literature=True,
        project_dir=str(project_dir),
        use_llm=False,
    )

    updated = ScientificKnowledgeAgent(use_llm=False, literature_client=disabled_literature_client).run(state)

    roles = {item["role"] for item in updated.literature_summary["local_file_insights"]}
    assert "planning_note" in roles
    assert "primary_paper" in roles
    assert "source_index" in roles


def test_scientific_knowledge_agent_infers_project_folder_under_projects_root(tmp_path, disabled_literature_client):
    projects_root = tmp_path / "projects"
    project_dir = projects_root / "ni3al_l12_calibration"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "literature_note.md").write_text("Ni3Al crystal plasticity literature note", encoding="utf-8")
    (project_dir / "stress_strain.csv").write_text("strain,stress\n0.0,0.0\n0.01,100.0\n", encoding="utf-8")

    state = ResearchState(
        user_goal="Calibrate Ni3Al using tensile stress-strain data.",
        workflow_type="calibration",
        material_system="ni3al_l12",
        needs_literature=False,
        needs_experimental_data=True,
        use_llm=False,
    )

    updated = ScientificKnowledgeAgent(
        use_llm=False,
        literature_client=disabled_literature_client,
        projects_root=projects_root,
    ).run(state)

    assert updated.project_dir == str(project_dir)
    assert updated.project_name == "ni3al_l12_calibration"
    assert any(path.endswith("stress_strain.csv") for path in updated.experimental_files)
    assert updated.experimental_data["status"] == "experimental_data_loaded"


def test_scientific_knowledge_agent_selects_relevant_case_and_ignores_gitkeep(tmp_path, disabled_literature_client):
    projects_root = tmp_path / "projects"
    project_dir = projects_root / "ni3al_l12"
    (project_dir / "experimental" / "single_crystal_tensile" / "raw").mkdir(parents=True, exist_ok=True)
    (project_dir / "experimental" / "cold_rolling_anisotropy" / "raw").mkdir(parents=True, exist_ok=True)
    (project_dir / "literature" / "cold_rolling_anisotropy" / "notes").mkdir(parents=True, exist_ok=True)
    (project_dir / "experimental" / "single_crystal_tensile" / "raw" / ".gitkeep").write_text("", encoding="utf-8")
    (project_dir / "experimental" / "single_crystal_tensile" / "raw" / "Ni3Al17-A1.txt").write_text(
        "true_stress,true_strain\n100,0.01\n",
        encoding="utf-8",
    )
    (project_dir / "experimental" / "cold_rolling_anisotropy" / "raw" / "rolling_curve.csv").write_text(
        "strain,stress\n0.0,0.0\n0.1,200.0\n",
        encoding="utf-8",
    )
    (project_dir / "literature" / "cold_rolling_anisotropy" / "notes" / "reading_notes.md").write_text(
        "Cold rolling note",
        encoding="utf-8",
    )

    state = ResearchState(
        user_goal="Calibrate xi_0_sl for Ni3Al using single tensile stress-strain data.",
        workflow_type="calibration",
        material_system="ni3al_l12",
        needs_literature=False,
        needs_experimental_data=True,
        use_llm=False,
    )

    updated = ScientificKnowledgeAgent(
        use_llm=False,
        literature_client=disabled_literature_client,
        projects_root=projects_root,
    ).run(state)

    assert any(path.endswith("Ni3Al17-A1.txt") for path in updated.experimental_files)
    assert not any("rolling_curve.csv" in path for path in updated.experimental_files)
    assert not any(path.endswith(".gitkeep") for path in updated.experimental_files)
    assert not any("cold_rolling_anisotropy" in path for path in updated.literature_files)

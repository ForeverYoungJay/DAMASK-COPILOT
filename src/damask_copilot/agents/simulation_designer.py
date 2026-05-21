"""Simulation design agent for the v1 workflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from damask_copilot.graph.state import ResearchState
from damask_copilot.memory.scientific_memory import ScientificMemoryLayer
from damask_copilot.schemas.files import GeneratedFiles
from damask_copilot.tools.damask_yaml import build_load_yaml, build_material_yaml, build_numerics_yaml
from damask_copilot.tools.geometry import build_grid_geometry
from damask_copilot.tools.optimization import propose_next_parameters


class SimulationDesignerAgent:
    """Convert the project plan into a concrete DAMASK simulation task and input set."""

    name = "simulation_designer"

    def __init__(self, workspace_root: str = "workspaces", scientific_memory: ScientificMemoryLayer | None = None) -> None:
        self.workspace_root = Path(workspace_root)
        self.scientific_memory = scientific_memory or ScientificMemoryLayer(workspace_root=self.workspace_root)

    def run(self, state: ResearchState) -> ResearchState:
        project_plan = dict(state.project_plan or {})
        known_parameters = dict(state.known_parameters or {})
        literature = dict(state.literature_summary or {})
        experimental = dict(state.experimental_data or {})
        previous_spec = dict(state.simulation_spec or {})
        workflow_type = state.workflow_type or "simulation_run"
        material_system = state.material_system or "generic_material"

        candidate = self._select_candidate_simulation(project_plan)
        compute_budget = dict(project_plan.get("compute_budget") or {})
        project_context = dict(project_plan.get("project_context") or {})
        parameter_priors = dict(project_plan.get("parameter_priors") or {})
        legacy_plan = state.simulation_plan
        legacy_geometry = getattr(legacy_plan, "geometry", None)
        legacy_loading = getattr(legacy_plan, "loading", None)

        nominal_parameters = self._nominal_parameters(known_parameters, state)
        nominal_parameters.update(dict(previous_spec.get("parameter_values", {})))
        parameter_ranges = self._parameter_ranges(nominal_parameters, workflow_type)
        geometry_spec = self._geometry_spec(state=state, compute_budget=compute_budget, legacy_geometry=legacy_geometry, candidate=candidate)
        loading_spec = self._loading_spec(state=state, workflow_type=workflow_type, legacy_loading=legacy_loading, candidate=candidate)
        strategy = self._modeling_strategy(material_system=material_system, workflow_type=workflow_type, candidate=candidate, geometry_spec=geometry_spec)
        expected_observables = list(project_plan.get("validation_metrics", [])) or list(experimental.get("observable_candidates", [])) or ["stress_strain_curve"]

        workspace_name = self._workspace_name(state=state, material_system=material_system, workflow_type=workflow_type, candidate=candidate)
        state.workspace = state.workspace or str(self.workspace_root / workspace_name)
        workspace = Path(state.workspace)
        workspace.mkdir(parents=True, exist_ok=True)

        simulation_spec = {
            "task_type": candidate.get("simulation_type_hint") or workflow_type,
            "workflow_type": workflow_type,
            "material_system": material_system,
            "candidate_simulation": candidate,
            "project_context": {
                "project_name": project_context.get("project_name") or state.project_name,
                "project_dir": project_context.get("project_dir") or state.project_dir,
                "experimental_files": list(project_context.get("experimental_files", [])) or list(state.experimental_files),
                "literature_files": list(project_context.get("literature_files", [])) or list(state.literature_files),
                "evidence_summary": dict(project_context.get("project_evidence") or {}),
            },
            "parameter_priors": {
                "parameter_source": parameter_priors.get("parameter_source") or known_parameters.get("source"),
                "database_record": dict(parameter_priors.get("database_record") or {}),
                "reported_cp_parameters": dict(parameter_priors.get("reported_cp_parameters") or known_parameters.get("reported_cp_parameters", {})),
                "elastic_constants": dict(parameter_priors.get("elastic_constants") or known_parameters.get("elastic_constants", {})),
                "phase_information": dict(parameter_priors.get("phase_information") or known_parameters.get("phase_information", {})),
                "data_policy": dict(parameter_priors.get("data_policy") or {}),
            },
            "hypothesis_targets": list(candidate.get("target_hypotheses", [])),
            "solver_strategy": strategy["solver_strategy"],
            "modeling_strategy": strategy,
            "geometry_strategy": geometry_spec,
            "loading_strategy": loading_spec,
            "material_model_choice": self._material_model_choice(known_parameters),
            "parameter_nominal_values": nominal_parameters,
            "parameter_ranges": parameter_ranges,
            "parameter_values": nominal_parameters,
            "expected_observables": expected_observables,
            "validation_metrics": list(project_plan.get("validation_metrics", [])) or expected_observables,
            "rationale": self._rationale(state, project_plan, candidate, strategy, literature),
            "input_data_contract": {
                "project_context_source": "projects/<project_name>/ and attached project files",
                "parameter_prior_source": "demo dataset today; SQL-backed parameter database in the future",
            },
            "phase_name": self._phase_name(known_parameters, material_system),
            "lattice": self._lattice(known_parameters),
            "elastic": dict(known_parameters.get("elastic_constants", {})),
            "plastic": nominal_parameters,
            "grid_type": geometry_spec["grid_type"],
            "cells": geometry_spec["cells"],
            "size": geometry_spec["size"],
            "grains": geometry_spec["grains"],
            "steps": loading_spec["steps"],
            "final_strain": loading_spec["final_strain"],
            "strain_rate": loading_spec["strain_rate"],
            "loading_mode": loading_spec["mode"],
            "loading_direction": loading_spec["direction"],
            "time": loading_spec["time"],
            "material_indices": [0],
            "orientation": [1.0, 0.0, 0.0, 0.0],
        }
        simulation_spec.update({
            key: value
            for key, value in previous_spec.items()
            if key in {
                "task_type",
                "solver_strategy",
                "geometry_strategy",
                "loading_strategy",
                "material_model_choice",
                "parameter_nominal_values",
                "parameter_ranges",
                "parameter_values",
                "rationale",
                "phase_name",
                "lattice",
                "elastic",
                "plastic",
                "grid_type",
                "cells",
                "size",
                "grains",
                "steps",
                "final_strain",
                "strain_rate",
                "loading_mode",
                "loading_direction",
                "time",
                "material_indices",
                "orientation",
            }
        })
        state.simulation_spec = simulation_spec

        state.material_yaml_path = build_material_yaml(simulation_spec, str(workspace / "material.yaml"))
        state.load_yaml_path = build_load_yaml(simulation_spec, str(workspace / "load.yaml"))
        state.numerics_yaml_path = build_numerics_yaml(simulation_spec, str(workspace / "numerics.yaml"))
        state.geometry_path = build_grid_geometry(simulation_spec, str(workspace / "geometry.vti"))
        self._write_research_state_snapshot(state, workspace / "research_state.json")
        state.generated_files = GeneratedFiles(
            workspace_dir=str(workspace),
            geometry_path=state.geometry_path,
            load_path=state.load_yaml_path,
            material_path=state.material_yaml_path,
            numerics_path=state.numerics_yaml_path,
            research_state_path=str(workspace / "research_state.json"),
            result_path=str(workspace / "results" / "result.hdf5"),
            report_path=str(workspace / "research_report.md"),
        )
        self.scientific_memory.remember_simulation_design(state)
        return state.append_trace(
            self.name,
            "simulation_designed",
            {
                "workspace": state.workspace,
                "task_type": simulation_spec["task_type"],
                "candidate_id": candidate.get("simulation_id"),
            },
        )

    def repair_from_validation(self, state: ResearchState) -> ResearchState:
        errors = [str(item) for item in (state.validation_result or {}).get("errors", [])]
        if state.simulation_spec is None:
            state.simulation_spec = {}
        spec = dict(state.simulation_spec)

        lowered = " ".join(errors).lower()
        if "material index" in lowered or "more materials requested" in lowered:
            spec["material_indices"] = [0]
            spec["grains"] = min(int(spec.get("grains", 1)), 1)
        if "missing homogenization" in lowered:
            spec["homogenization_name"] = "SX"
        if "missing phase" in lowered:
            spec["phase_name"] = spec.get("phase_name") or spec.get("material_system", "phase_0")
        if ".o must be a quaternion" in lowered or "orientation" in lowered:
            spec["orientation"] = [1.0, 0.0, 0.0, 0.0]
        if "plastic block must define a 'type'" in lowered:
            plastic = dict(spec.get("plastic", {}))
            plastic["type"] = plastic.get("type") or "phenopowerlaw"
            spec["plastic"] = plastic
            spec["parameter_values"] = plastic
        if "load.yaml must define a non-empty loadstep list" in lowered:
            spec["steps"] = max(1, int(spec.get("steps", 5)))

        state.simulation_spec = spec
        return self.run(state).append_trace(self.name, "repaired_from_validation", {"error_count": len(errors)})

    def repair_from_error(self, state: ResearchState) -> ResearchState:
        detected = dict((state.run_result or {}).get("detected_errors", {}))
        matched = list(detected.get("matched_errors", []))
        if state.simulation_spec is None:
            state.simulation_spec = {}
        spec = dict(state.simulation_spec)

        if "material_index_out_of_bounds" in matched or "material_count_mismatch" in matched:
            spec["material_indices"] = [0]
            spec["grains"] = 1
        if "missing_file_or_executable" in matched:
            spec["solver_strategy"] = "spectral_basic_safe_fallback"
            spec["cells"] = [8, 8, 8]
        elif state.mode != "dry_run":
            spec["cells"] = [8, 8, 8]
            spec["grains"] = min(int(spec.get("grains", 4)), 4)
            spec["steps"] = min(int(spec.get("steps", 10)), 5)

        state.simulation_spec = spec
        return self.run(state).append_trace(self.name, "repaired_from_error", {"matched_errors": matched})

    def _select_candidate_simulation(self, project_plan: dict[str, Any]) -> dict[str, Any]:
        candidates = list(project_plan.get("candidate_simulations", []) or [])
        if not candidates:
            return {
                "simulation_id": "SIM-1",
                "title": "Baseline DAMASK study",
                "objective": "Establish a first executable DAMASK baseline.",
                "why_needed": "A first simulation is needed to connect the project plan to executable DAMASK inputs.",
                "target_hypotheses": ["H1"],
                "required_evidence": [],
                "simulation_type_hint": project_plan.get("workflow_type", "simulation_run"),
                "priority": 1,
            }
        prioritized = sorted(candidates, key=lambda item: int(item.get("priority", 999)))
        return dict(prioritized[0])

    def _nominal_parameters(self, known_parameters: dict[str, Any], state: ResearchState) -> dict[str, Any]:
        base = dict(known_parameters.get("reported_cp_parameters", {}))
        latest_history = state.parameter_history[-1] if state.parameter_history else {}
        proposed = propose_next_parameters(state.parameter_history, {"step_scale": 0.98})
        merged = dict(base)
        merged.update(dict(latest_history.get("parameters", {})))
        merged.update(dict(proposed.get("parameters", {})))
        return merged

    def _parameter_ranges(self, nominal_parameters: dict[str, Any], workflow_type: str) -> dict[str, Any]:
        ranges: dict[str, Any] = {}
        scale = 0.2 if workflow_type == "calibration" else 0.1
        for key, value in nominal_parameters.items():
            if isinstance(value, list) and value and isinstance(value[0], (int, float)):
                center = float(value[0])
                ranges[key] = {"min": center * (1.0 - scale), "max": center * (1.0 + scale)}
            elif isinstance(value, (int, float)):
                center = float(value)
                ranges[key] = {"min": center * (1.0 - scale), "max": center * (1.0 + scale)}
        return ranges

    def _geometry_spec(self, *, state: ResearchState, compute_budget: dict[str, Any], legacy_geometry, candidate: dict[str, Any]) -> dict[str, Any]:
        recommended_cells = list(compute_budget.get("recommended_cells", [])) or [8, 8, 8]
        recommended_grains = int(compute_budget.get("recommended_grains", 4))
        task_hint = str(candidate.get("simulation_type_hint", "")).lower()
        is_single_crystal = "single_crystal" in task_hint or "single crystal" in state.user_goal.lower()
        cells = list(getattr(legacy_geometry, "cells", recommended_cells))
        grains = int(getattr(legacy_geometry, "grains", 1 if is_single_crystal else recommended_grains))
        return {
            "grid_type": getattr(legacy_geometry, "grid_type", "voronoi"),
            "cells": cells,
            "size": list(getattr(legacy_geometry, "size", [1.0, 1.0, 1.0])),
            "grains": 1 if is_single_crystal else max(1, grains),
            "representation": "single_crystal" if is_single_crystal else "polycrystal_rve",
        }

    def _loading_spec(self, *, state: ResearchState, workflow_type: str, legacy_loading, candidate: dict[str, Any]) -> dict[str, Any]:
        objective_text = f"{state.user_goal} {candidate.get('simulation_type_hint', '')}".lower()
        if "compression" in objective_text:
            mode = "uniaxial_compression"
        elif "rolling" in objective_text:
            mode = "plane_strain_rolling_proxy"
        elif "shear" in objective_text:
            mode = "simple_shear"
        else:
            mode = getattr(legacy_loading, "mode", "uniaxial_tension")
        return {
            "mode": mode,
            "direction": getattr(legacy_loading, "direction", "x"),
            "final_strain": float(getattr(legacy_loading, "final_strain", 0.02 if workflow_type != "calibration" else 0.03)),
            "strain_rate": float(getattr(legacy_loading, "strain_rate", 1.0e-3)),
            "steps": int(getattr(legacy_loading, "steps", 10 if state.mode == "dry_run" else 25)),
            "time": 1.0,
        }

    def _modeling_strategy(self, *, material_system: str, workflow_type: str, candidate: dict[str, Any], geometry_spec: dict[str, Any]) -> dict[str, Any]:
        representation = geometry_spec["representation"]
        return {
            "simulation_abstraction": representation,
            "solver_strategy": "spectral_basic",
            "geometry_strategy": geometry_spec["grid_type"],
            "loading_proxy": candidate.get("simulation_type_hint") or workflow_type,
            "target_material": material_system,
            "requires_orientation_population": geometry_spec["grains"] > 1,
        }

    def _material_model_choice(self, known_parameters: dict[str, Any]) -> str:
        plastic = dict(known_parameters.get("reported_cp_parameters", {}))
        return str(plastic.get("type") or known_parameters.get("phase_information", {}).get("phase_type") or "phenopowerlaw")

    def _rationale(
        self,
        state: ResearchState,
        project_plan: dict[str, Any],
        candidate: dict[str, Any],
        strategy: dict[str, Any],
        literature: dict[str, Any],
    ) -> str:
        basis = literature.get("summary") or "limited literature evidence"
        return (
            f"Selected {candidate.get('simulation_id')} as the highest-priority executable task. "
            f"Using a {strategy['simulation_abstraction']} representation with {strategy['solver_strategy']} "
            f"to address the {state.workflow_type or 'simulation'} workflow. "
            f"Planning is guided by: {basis}. "
            f"Validation target: {', '.join(project_plan.get('validation_metrics', []) or ['stress_strain_curve'])}."
        )

    def _phase_name(self, known_parameters: dict[str, Any], material_system: str) -> str:
        phase_info = dict(known_parameters.get("phase_information", {}))
        return str(phase_info.get("phase_name") or material_system)

    def _lattice(self, known_parameters: dict[str, Any]) -> str:
        phase_info = dict(known_parameters.get("phase_information", {}))
        return str(phase_info.get("lattice") or "cF")

    def _workspace_name(self, *, state: ResearchState, material_system: str, workflow_type: str, candidate: dict[str, Any]) -> str:
        candidate_id = str(candidate.get("simulation_id") or "sim")
        return self._slugify(f"{material_system}_{workflow_type}_{candidate_id}")

    def _write_research_state_snapshot(self, state: ResearchState, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = state.model_dump()
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def _slugify(value: str | None) -> str:
        text = (value or "damask_workflow").lower().replace(" ", "_")
        return "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in text).strip("_")

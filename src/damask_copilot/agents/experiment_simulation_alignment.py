"""Experiment-simulation alignment agent."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

from damask_copilot.graph.materials_research_state import MaterialsResearchState, append_trace
from damask_copilot.llm.prompts import load_prompt
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.schemas.llm_outputs import AlignmentInterpretationOutput


class ExperimentSimulationAlignmentAgent:
    """Align available experimental observables with simulation outputs."""

    name = "experiment_simulation_alignment"

    def __init__(
        self,
        *,
        use_llm: bool = False,
        model_name: str | None = None,
        llm_runner: StructuredLLMRunner | None = None,
    ) -> None:
        self.use_llm = use_llm
        self.model_name = model_name
        self.llm_runner = llm_runner

    def run(self, state: MaterialsResearchState) -> MaterialsResearchState:
        updated = self._run_deterministic(state)
        if self.use_llm or state.get("use_llm", False):
            return self._run_llm(state, updated)
        return updated

    def _run_deterministic(self, state: MaterialsResearchState) -> MaterialsResearchState:
        experimental_data = dict(state.get("experimental_data_summary") or {})
        postprocess_report = state.get("postprocess_report")
        if not experimental_data or experimental_data.get("status") == "experimental_data_missing":
            updated = dict(state)
            updated["alignment_report"] = {
                "status": "not_applicable",
                "summary": "No experimental dataset was provided, so no experiment-simulation alignment was attempted.",
                "compared_observables": [],
                "metrics": {},
                "notes": [],
                "requires_human_review": False,
            }
            return append_trace(updated, self.name, "alignment_not_applicable", {})

        if postprocess_report is None or getattr(postprocess_report, "stress_strain_csv", None) is None:
            updated = dict(state)
            updated["alignment_report"] = {
                "status": "comparison_not_possible",
                "summary": "Simulation outputs are insufficient for direct comparison with the supplied experimental data.",
                "compared_observables": [],
                "metrics": {},
                "notes": ["Run post-processing that extracts observables matching the experiment."],
                "requires_human_review": True,
            }
            return append_trace(updated, self.name, "alignment_pending", {})

        simulated_rows = self._read_table(Path(postprocess_report.stress_strain_csv))
        simulated_columns = list(simulated_rows[0].keys()) if simulated_rows else []
        experimental_columns: list[str] = []
        experimental_rows: list[dict[str, Any]] = []
        for dataset in experimental_data.get("datasets", []):
            for column in dataset.get("columns", []):
                if column not in experimental_columns:
                    experimental_columns.append(column)
            dataset_path = dataset.get("path")
            if dataset_path and str(dataset.get("format")) in {"csv", "json"}:
                experimental_rows.extend(self._read_table(Path(dataset_path)))

        compared: list[str] = []
        metrics: dict[str, Any] = {}
        notes: list[str] = []
        if any("stress" in item.lower() for item in simulated_columns) and any("stress" in item.lower() for item in experimental_columns):
            compared.append("stress")
        if any("strain" in item.lower() for item in simulated_columns) and any("strain" in item.lower() for item in experimental_columns):
            compared.append("strain")
        if not compared:
            notes.append("Observable names could not be matched directly between experimental and simulated outputs.")

        numeric_metrics = self._compare_stress_strain_curves(simulated_rows, experimental_rows, experimental_columns)
        if numeric_metrics:
            metrics.update(numeric_metrics)
            if "stress" not in compared:
                compared.append("stress")
            if "strain" not in compared:
                compared.append("strain")
        notes.append("Stress/strain definitions and units may require manual confirmation before quantitative comparison.")

        updated = dict(state)
        updated["alignment_report"] = {
            "status": "aligned" if compared else "comparison_not_possible",
            "summary": "Experiment and simulation observables were aligned at a metadata level." if compared else "Metadata-level comparison was inconclusive.",
            "compared_observables": compared,
            "metrics": metrics,
            "notes": notes,
            "requires_human_review": not bool(compared),
        }
        return append_trace(updated, self.name, "alignment_completed", {
            "compared_observables": compared,
            "requires_human_review": not bool(compared),
            "metric_keys": sorted(metrics.keys()),
        })

    def _run_llm(self, original_state: MaterialsResearchState, summarized_state: MaterialsResearchState) -> MaterialsResearchState:
        alignment = dict(summarized_state.get("alignment_report") or {})
        if alignment.get("status") == "not_applicable":
            return summarized_state

        runner = self.llm_runner or StructuredLLMRunner(model_name=original_state.get("model") or self.model_name)
        parsed = runner.run_structured(
            prompt_name="experiment_simulation_alignment",
            system_prompt=load_prompt("experiment_simulation_alignment"),
            user_prompt=(
                f"User query: {original_state.get('user_query')}\n"
                f"Experimental data summary: {json.dumps(original_state.get('experimental_data_summary') or {}, ensure_ascii=False)}\n"
                f"Simulation plan: {json.dumps(self._jsonable(original_state.get('simulation_plan')), ensure_ascii=False)}\n"
                f"Deterministic alignment report: {json.dumps(alignment, ensure_ascii=False)}"
            ),
            output_schema=AlignmentInterpretationOutput,
            model_name=original_state.get("model") or self.model_name,
        )
        updated = dict(summarized_state)
        alignment["summary"] = parsed.summary or alignment.get("summary", "")
        notes = list(alignment.get("notes", []))
        for item in parsed.likely_mismatch_causes + parsed.recommended_actions:
            if item not in notes:
                notes.append(item)
        alignment["notes"] = notes
        alignment["llm_interpretation"] = parsed.model_dump()
        alignment["requires_human_review"] = bool(alignment.get("requires_human_review") or parsed.confidence == "low")
        updated["alignment_report"] = alignment
        return append_trace(updated, self.name, "alignment_interpreted_llm", {
            "confidence": parsed.confidence,
            "recommended_actions": len(parsed.recommended_actions),
        })

    @staticmethod
    def _read_columns(path: Path) -> list[str]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            first_row = next(reader, [])
        return [str(item) for item in first_row]

    def _read_table(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        if path.suffix.lower() == ".csv":
            with path.open("r", encoding="utf-8") as handle:
                return list(csv.DictReader(handle))
        if path.suffix.lower() == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, list) and payload and isinstance(payload[0], dict):
                return payload
        return []

    def _compare_stress_strain_curves(
        self,
        simulated_rows: list[dict[str, Any]],
        experimental_rows: list[dict[str, Any]],
        experimental_columns: list[str],
    ) -> dict[str, Any]:
        if not simulated_rows or not experimental_rows:
            return {}
        sim_strain_col, sim_stress_col = self._find_strain_stress_columns(list(simulated_rows[0].keys()))
        exp_strain_col, exp_stress_col = self._find_strain_stress_columns(experimental_columns)
        if not sim_strain_col or not sim_stress_col or not exp_strain_col or not exp_stress_col:
            return {}
        sim_curve = self._extract_curve(simulated_rows, sim_strain_col, sim_stress_col)
        exp_curve = self._extract_curve(experimental_rows, exp_strain_col, exp_stress_col)
        if len(sim_curve) < 2 or len(exp_curve) < 2:
            return {}

        exp_x = [x for x, _ in exp_curve]
        exp_y = [y for _, y in exp_curve]
        sim_interp_y: list[float] = []
        exp_interp_y: list[float] = []
        for x, y in sim_curve:
            interp = self._interpolate(exp_x, exp_y, x)
            if interp is None:
                continue
            sim_interp_y.append(y)
            exp_interp_y.append(interp)
        if len(sim_interp_y) < 2:
            return {}
        rmse = math.sqrt(sum((a - b) ** 2 for a, b in zip(sim_interp_y, exp_interp_y)) / len(sim_interp_y))
        mae = sum(abs(a - b) for a, b in zip(sim_interp_y, exp_interp_y)) / len(sim_interp_y)
        return {
            "rmse": rmse,
            "mae": mae,
            "comparison_points": len(sim_interp_y),
            "simulated_columns": [sim_strain_col, sim_stress_col],
            "experimental_columns": [exp_strain_col, exp_stress_col],
        }

    def _find_strain_stress_columns(self, columns: list[str]) -> tuple[str | None, str | None]:
        strain = None
        stress = None
        for column in columns:
            lowered = column.lower()
            if strain is None and "strain" in lowered:
                strain = column
            if stress is None and "stress" in lowered:
                stress = column
        return strain, stress

    def _extract_curve(self, rows: list[dict[str, Any]], x_column: str, y_column: str) -> list[tuple[float, float]]:
        curve: list[tuple[float, float]] = []
        for row in rows:
            try:
                x = float(row[x_column])
                y = float(row[y_column])
            except (KeyError, TypeError, ValueError):
                continue
            if "%" in x_column.lower():
                x /= 100.0
            curve.append((x, y))
        curve.sort(key=lambda item: item[0])
        return curve

    def _interpolate(self, xs: list[float], ys: list[float], target: float) -> float | None:
        if not xs or target < xs[0] or target > xs[-1]:
            return None
        for index in range(1, len(xs)):
            x0, x1 = xs[index - 1], xs[index]
            if x0 <= target <= x1:
                if x1 == x0:
                    return ys[index]
                fraction = (target - x0) / (x1 - x0)
                return ys[index - 1] + fraction * (ys[index] - ys[index - 1])
        return None

    @staticmethod
    def _jsonable(value: Any) -> Any:
        if value is None:
            return None
        dumper = getattr(value, "model_dump", None)
        if dumper is not None:
            return dumper()
        if hasattr(value, "dict"):
            return value.dict()
        return value

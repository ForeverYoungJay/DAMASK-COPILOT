"""DAMASK execution agent for the v1 workflow."""

from __future__ import annotations

from pathlib import Path

from damask_copilot.graph.state import ResearchState
from damask_copilot.tools.execution import collect_result_files, parse_damask_log, run_damask_grid


class DAMASKExecutionAgent:
    """Tool-driven DAMASK execution wrapper with structured failure handling."""

    name = "damask_execution"

    def run(self, state: ResearchState) -> ResearchState:
        if not state.needs_damask_simulation:
            state.run_result = {
                "ok": True,
                "status": "skipped",
                "result_files": [],
                "message": "Workflow does not require DAMASK execution.",
                "failure_category": None,
            }
            return state.append_trace(self.name, "execution_skipped", {"reason": "workflow_does_not_require_simulation"})

        if state.mode == "dry_run":
            workdir = Path(state.workspace or "workspaces/dry_run")
            workdir.mkdir(parents=True, exist_ok=True)
            log_path = workdir / "run.log"
            log_path.write_text("Dry run: DAMASK execution skipped.\n", encoding="utf-8")
            state.run_result = {
                "ok": True,
                "status": "skipped",
                "log_path": str(log_path),
                "result_files": [],
                "message": "Dry run: execution skipped.",
                "failure_category": None,
            }
            return state.append_trace(self.name, "execution_skipped", {"reason": "dry_run"})

        missing_inputs = [
            key
            for key, value in {
                "geometry_path": state.geometry_path,
                "load_yaml_path": state.load_yaml_path,
                "material_yaml_path": state.material_yaml_path,
            }.items()
            if not value
        ]
        if missing_inputs:
            state.run_result = {
                "ok": False,
                "status": "failed",
                "result_files": [],
                "message": f"Missing execution inputs: {missing_inputs}",
                "failure_category": "input",
            }
            return state.append_trace(self.name, "execution_failed_preflight", {"missing_inputs": missing_inputs})

        state.run_result = run_damask_grid(
            geometry_path=state.geometry_path or "",
            load_yaml_path=state.load_yaml_path or "",
            material_yaml_path=state.material_yaml_path or "",
            workdir=state.workspace or "workspaces/damask_execution",
        )

        if state.run_result.get("ok") and not state.run_result.get("result_files"):
            collected = collect_result_files(state.workspace or "workspaces/damask_execution")
            if collected.get("ok"):
                state.run_result["result_files"] = list(collected.get("result_files", []))
                state.run_result["result_file_count"] = collected.get("count", 0)

        log_path = state.run_result.get("log_path")
        if log_path:
            state.run_result["log_summary"] = parse_damask_log(log_path)
        state.run_result["execution_decision"] = self._execution_decision(state.run_result)
        return state.append_trace(
            self.name,
            "execution_finished",
            {
                "status": state.run_result.get("status"),
                "failure_category": state.run_result.get("failure_category"),
            },
        )

    @staticmethod
    def _execution_decision(run_result: dict) -> dict[str, str]:
        status = run_result.get("status")
        failure_category = run_result.get("failure_category")
        if status == "success":
            return {"action": "postprocess", "reason": "Execution completed successfully."}
        if status == "not_available":
            return {"action": "repair_or_stub", "reason": "DAMASK is unavailable in the current environment."}
        if failure_category == "input":
            return {"action": "repair_inputs", "reason": "Execution failed due to an input/configuration problem."}
        if failure_category == "model":
            return {"action": "change_model", "reason": "Execution suggests a constitutive/model-definition issue."}
        if failure_category == "environment":
            return {"action": "check_environment", "reason": "Execution failed because the environment or executable is unavailable."}
        return {"action": "repair_and_retry", "reason": "Execution failed and should be reviewed before retrying."}

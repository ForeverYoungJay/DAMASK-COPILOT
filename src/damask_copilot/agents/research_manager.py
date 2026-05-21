"""Research manager agent."""

from __future__ import annotations

from damask_copilot.agents.base import BaseAgent
from damask_copilot.graph.state import ResearchState as WorkflowResearchState
from damask_copilot.llm.prompts import load_prompt
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.schemas.llm_outputs import ResearchManagerOutput
from damask_copilot.schemas.research_goal import ResearchGoal
from damask_copilot.schemas.research_state import ResearchState as LegacyResearchState


class ResearchManagerAgent(BaseAgent):
    """Infer a research goal and initialize the workflow."""

    name = "research_manager"

    def __init__(self, *, use_llm: bool = False, model_name: str | None = None, llm_runner: StructuredLLMRunner | None = None) -> None:
        self.use_llm = use_llm
        self.model_name = model_name
        self.llm_runner = llm_runner

    def run(self, state):
        if isinstance(state, WorkflowResearchState):
            return self._run_v1(state)
        if self.use_llm or state.use_llm:
            return self._run_llm(state)
        return self._run_deterministic(state)

    def _run_v1(self, state: WorkflowResearchState) -> WorkflowResearchState:
        goal = state.user_goal.strip()
        lowered = goal.lower()
        manager_output = self._infer_manager_output_from_text(goal, lowered)
        if self.use_llm or state.use_llm:
            manager_output = self._run_llm_for_v1(state, default=manager_output)

        state.workflow_type = manager_output.workflow_type
        state.material_system = manager_output.material_system
        state.objective = manager_output.objective
        state.reasoning_summary = manager_output.reasoning_summary
        state.research_manager_output = self.model_dump(manager_output)
        state.needs_literature = manager_output.needs_literature
        state.needs_experimental_data = manager_output.needs_experimental_data
        state.needs_damask_simulation = manager_output.needs_damask_simulation
        state.needs_parameter_optimization = manager_output.needs_parameter_optimization
        state.needs_report = manager_output.needs_report
        if state.max_iterations <= 0:
            state.max_iterations = 3
        state.iteration = max(0, state.iteration)
        state.next_action = {"type": "continue", "reason": "Research workflow initialized."}
        return state.append_trace(
            self.name,
            "workflow_initialized",
            {
                "workflow_type": state.workflow_type,
                "material_system": state.material_system,
                "objective": state.objective,
                "needs_literature": state.needs_literature,
                "needs_experimental_data": state.needs_experimental_data,
                "needs_damask_simulation": state.needs_damask_simulation,
                "needs_parameter_optimization": state.needs_parameter_optimization,
                "needs_report": state.needs_report,
                "max_iterations": state.max_iterations,
            },
        )

    def _run_llm(self, state: LegacyResearchState) -> LegacyResearchState:
        runner = self.llm_runner or StructuredLLMRunner(model_name=state.model_name or self.model_name)
        parsed = runner.run_structured(
            prompt_name="research_manager",
            system_prompt=load_prompt("research_manager"),
            user_prompt=f"User query: {state.user_query}",
            output_schema=ResearchManagerOutput,
            model_name=state.model_name or self.model_name,
        )
        parsed = self._merged_output_from_query(state.user_query, parsed)
        state.research_manager_output = parsed
        state.goal = ResearchGoal(
            user_query=state.user_query,
            material_system=parsed.material_system,
            objective=parsed.objective,
        )
        state.status = "goal_defined"
        return self.add_trace(state, "goal_inferred_llm", self.model_dump(parsed))

    def _run_deterministic(self, state: LegacyResearchState) -> LegacyResearchState:
        query = state.user_query.strip()
        lowered = query.lower()
        parsed = self._infer_manager_output_from_text(query, lowered)

        state.goal = ResearchGoal(
            user_query=query,
            material_system=parsed.material_system,
            objective=parsed.objective,
        )
        state.research_manager_output = parsed
        state.status = "goal_defined"
        return self.add_trace(
            state,
            "goal_inferred",
            self.model_dump(parsed),
        )

    def _run_llm_for_v1(self, state: WorkflowResearchState, *, default: ResearchManagerOutput) -> ResearchManagerOutput:
        try:
            runner = self.llm_runner or StructuredLLMRunner(model_name=state.model or self.model_name)
            parsed = runner.run_structured(
                prompt_name="research_manager",
                system_prompt=load_prompt("research_manager"),
                user_prompt=f"User query: {state.user_goal}",
                output_schema=ResearchManagerOutput,
                model_name=state.model or self.model_name,
            )
            return self._merged_output_from_query(state.user_goal, parsed)
        except Exception:
            return default

    def _infer_manager_output_from_text(self, query: str, lowered: str) -> ResearchManagerOutput:
        workflow_type = self._classify_workflow_type(lowered)
        material_system = self._infer_material_system(lowered)
        objective = self._infer_objective(lowered, workflow_type)
        needs = self._infer_workflow_requirements(lowered, workflow_type)
        return ResearchManagerOutput(
            material_system=material_system,
            objective=objective,
            workflow_type=workflow_type,
            needs_literature=needs["needs_literature"],
            needs_experimental_data=needs["needs_experimental_data"],
            needs_damask_simulation=needs["needs_damask_simulation"],
            needs_parameter_optimization=needs["needs_parameter_optimization"],
            needs_report=needs["needs_report"],
            reasoning_summary=f"Deterministically classified '{query}' as a {workflow_type} workflow for {material_system}.",
        )

    def _merged_output_from_query(self, query: str, parsed: ResearchManagerOutput) -> ResearchManagerOutput:
        lowered = query.lower()
        inferred = self._infer_manager_output_from_text(query, lowered)
        payload = self.model_dump(parsed)
        payload["workflow_type"] = payload.get("workflow_type") or inferred.workflow_type
        payload["needs_literature"] = bool(payload.get("needs_literature", inferred.needs_literature))
        payload["needs_experimental_data"] = bool(payload.get("needs_experimental_data", inferred.needs_experimental_data))
        payload["needs_damask_simulation"] = bool(payload.get("needs_damask_simulation", inferred.needs_damask_simulation))
        payload["needs_parameter_optimization"] = bool(payload.get("needs_parameter_optimization", inferred.needs_parameter_optimization))
        payload["needs_report"] = bool(payload.get("needs_report", inferred.needs_report))
        if not payload.get("material_system"):
            payload["material_system"] = inferred.material_system
        if not payload.get("objective"):
            payload["objective"] = inferred.objective
        if not payload.get("reasoning_summary"):
            payload["reasoning_summary"] = inferred.reasoning_summary
        return ResearchManagerOutput.model_validate(payload)

    @staticmethod
    def _classify_workflow_type(lowered_goal: str) -> str:
        if any(token in lowered_goal for token in ["literature", "review", "survey"]):
            return "literature_review"
        if any(token in lowered_goal for token in ["input", "yaml", "geometry", "setup"]):
            return "damask_input_generation"
        if any(token in lowered_goal for token in ["calibration", "calibrat", "fit", "optimiz", "inverse"]):
            return "calibration"
        if any(token in lowered_goal for token in ["compare", "alignment", "experiment"]):
            return "experiment_simulation_comparison"
        if any(token in lowered_goal for token in ["discover", "closed-loop", "iterate", "screen"]):
            return "closed_loop_discovery"
        if any(token in lowered_goal for token in ["run", "simulate", "simulation"]):
            return "simulation_run"
        return "simulation_run"

    @staticmethod
    def _infer_objective(lowered_goal: str, workflow_type: str) -> str:
        if "calibrat" in lowered_goal or "fit" in lowered_goal or "optimiz" in lowered_goal:
            return "Calibrate a DAMASK crystal plasticity model against target observables."
        if "compression" in lowered_goal:
            return "Study response under uniaxial compression."
        if "tension" in lowered_goal or "tensile" in lowered_goal:
            return "Study response under uniaxial tension."
        if workflow_type == "literature_review":
            return "Review the relevant scientific literature and DAMASK modeling context."
        if workflow_type == "damask_input_generation":
            return "Generate DAMASK-ready input files for the requested study."
        return "Run a DAMASK-guided research workflow for the requested material system."

    @staticmethod
    def _infer_workflow_requirements(lowered_goal: str, workflow_type: str) -> dict[str, bool]:
        needs_literature = workflow_type in {"literature_review", "calibration", "experiment_simulation_comparison", "closed_loop_discovery"}
        needs_experimental_data = workflow_type in {"calibration", "experiment_simulation_comparison"}
        needs_damask_simulation = workflow_type not in {"literature_review"}
        needs_parameter_optimization = workflow_type in {"calibration", "closed_loop_discovery"} or any(
            token in lowered_goal for token in ["calibrat", "fit", "optimiz", "inverse"]
        )
        needs_report = True
        if workflow_type == "damask_input_generation":
            needs_literature = any(token in lowered_goal for token in ["doc", "documentation", "best practice", "literature"])
            needs_experimental_data = False
            needs_damask_simulation = False
            needs_parameter_optimization = False
        if workflow_type == "simulation_run":
            needs_experimental_data = any(token in lowered_goal for token in ["experiment", "data", "stress-strain", "tensile", "compression"])
        return {
            "needs_literature": needs_literature,
            "needs_experimental_data": needs_experimental_data,
            "needs_damask_simulation": needs_damask_simulation,
            "needs_parameter_optimization": needs_parameter_optimization,
            "needs_report": needs_report,
        }

    @staticmethod
    def _infer_material_system(lowered_goal: str) -> str:
        if "ni3al" in lowered_goal:
            return "ni3al_l12"
        if "fcc al" in lowered_goal or "aluminum" in lowered_goal or "aluminium" in lowered_goal:
            return "fcc_al"
        if "fcc cu" in lowered_goal or "copper" in lowered_goal:
            return "fcc_cu"
        if "nickel" in lowered_goal and "single crystal" in lowered_goal:
            return "single_crystal_ni"
        return "generic_material"

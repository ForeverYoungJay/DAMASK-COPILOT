# DAMASK Copilot Agents

This project is DAMASK Copilot, a closed-loop scientific discovery system for crystal plasticity simulation.

Use 7 core agents only:
1. ResearchManagerAgent
2. ScientificKnowledgeAgent
3. ProjectPlannerAgent
4. SimulationDesignerAgent
5. DAMASKExecutionAgent
6. AnalysisAndCriticAgent
7. ResearchReportAgent

Do not create many micro-agents for deterministic operations.

Deterministic tasks belong in `src/damask_copilot/tools/`.

DAMASK execution, preprocessing, validation, and post-processing should be exposed through MCP-compatible tools where possible.

Use typed state schemas.

Add tests for validation and state transition logic.

Keep changes small, reviewable, and covered by tests.

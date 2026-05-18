"""CLI entry points for DAMASK Copilot."""

from __future__ import annotations

import argparse
from pathlib import Path

from damask_copilot.graph.simple_runner import run_research_graph
from damask_copilot.schemas.research_state import ResearchState


def build_parser() -> argparse.ArgumentParser:
    """Build the project CLI parser."""
    parser = argparse.ArgumentParser(prog="damask-copilot")
    subparsers = parser.add_subparsers(dest="command", required=True)

    research_parser = subparsers.add_parser("research", help="Run the research pipeline.")
    research_parser.add_argument("query", help="Research query to analyze.")
    research_parser.add_argument("--dry-run", action="store_true", help="Skip execution and create a report only.")
    research_parser.add_argument("--llm", dest="use_llm", action="store_true", help="Enable LLM-backed selected agents.")
    research_parser.add_argument("--no-llm", dest="use_llm", action="store_false", help="Disable LLM-backed selected agents.")
    research_parser.add_argument("--model", dest="model_name", help="Override the LLM model name.")
    research_parser.add_argument("--smoke-test", action="store_true", help="Request a small smoke-test planning mode.")
    research_parser.set_defaults(use_llm=False)
    return parser


def main() -> int:
    """Run the CLI."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "research":
        state = ResearchState(
            user_query=args.query,
            dry_run=args.dry_run,
            use_llm=args.use_llm,
            model_name=args.model_name,
            smoke_test=args.smoke_test,
        )
        final_state = run_research_graph(state)
        report_path = final_state.report_path or str(Path("workspaces") / "damask_copilot_report.md")
        print(f"Completed research pipeline. Report: {report_path}")
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2

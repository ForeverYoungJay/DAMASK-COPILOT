"""CLI entry points for DAMASK Copilot."""

from __future__ import annotations

import argparse
from pathlib import Path

from damask_copilot.graph.runner import run_research_graph


def build_parser() -> argparse.ArgumentParser:
    """Build the project CLI parser."""
    parser = argparse.ArgumentParser(prog="damask-copilot")
    subparsers = parser.add_subparsers(dest="command", required=True)

    _add_run_parser(subparsers.add_parser("research", help="Run the research graph."))
    graph_parser = subparsers.add_parser("graph", help="LangGraph-based DAMASK Copilot workflows.")
    graph_subparsers = graph_parser.add_subparsers(dest="graph_command", required=True)
    _add_run_parser(graph_subparsers.add_parser("run", help="Run the LangGraph research workflow."))
    return parser


def _add_run_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("query", help="Research query text or a YAML goal file path.")
    parser.add_argument("--dry-run", action="store_true", help="Run planning only and skip execution.")
    parser.add_argument("--smoke-test", action="store_true", help="Run the smoke-test DAMASK workflow.")
    parser.add_argument("--full-run", dest="allow_full_run", action="store_true", help="Allow full execution mode.")
    parser.add_argument("--llm", dest="use_llm", action="store_true", help="Enable LLM-backed planning nodes.")
    parser.add_argument("--no-llm", dest="use_llm", action="store_false", help="Disable LLM-backed planning nodes.")
    parser.add_argument("--model", dest="model_name", help="Override the LLM model name.")
    parser.add_argument("--max-iterations", type=int, default=1, help="Maximum research iterations.")
    parser.add_argument("--thread-id", help="Reuse a specific LangGraph thread id when checkpointing in-process.")
    parser.add_argument("--overwrite", action="store_true", help="Allow overwriting generated workspaces.")
    parser.add_argument("--approve", action="store_true", help="Approve a full-run execution request.")
    parser.set_defaults(allow_full_run=False, use_llm=False)


def main() -> int:
    """Run the CLI."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "research" or (args.command == "graph" and args.graph_command == "run"):
        if args.approve and not args.allow_full_run:
            parser.error("--approve can only be used together with --full-run.")
        mode = _resolve_mode(args)
        final_state = run_research_graph(
            user_query=args.query,
            mode=mode,
            use_llm=args.use_llm,
            model=args.model_name,
            max_iterations=args.max_iterations,
            approve=args.approve,
            allow_overwrite=args.overwrite,
            thread_id=args.thread_id,
        )
        report_path = final_state.get("report_path") or str(Path("workspaces") / "damask_copilot_report.md")
        print(f"Completed research pipeline. Report: {report_path}")
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


def _resolve_mode(args: argparse.Namespace) -> str:
    if args.dry_run:
        return "dry_run"
    if args.smoke_test:
        return "smoke_test"
    if args.allow_full_run:
        return "full_run"
    return "dry_run"


if __name__ == "__main__":
    raise SystemExit(main())

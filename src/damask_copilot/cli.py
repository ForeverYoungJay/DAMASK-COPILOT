"""CLI entry points for DAMASK Copilot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from damask_copilot.graph.materials_research_graph import (
    resume_materials_research_graph,
    run_materials_research_graph,
)
from damask_copilot.graph.runner import run_research_graph


def build_parser() -> argparse.ArgumentParser:
    """Build the project CLI parser."""
    parser = argparse.ArgumentParser(prog="damask-copilot")
    subparsers = parser.add_subparsers(dest="command", required=True)

    _add_run_parser(subparsers.add_parser("research", help="Run the research graph."))
    materials_parser = subparsers.add_parser("materials", help="Run the generic materials research graph.")
    materials_subparsers = materials_parser.add_subparsers(dest="materials_command", required=True)
    _add_materials_run_parser(materials_subparsers.add_parser("run", help="Run the generic materials research workflow."))
    _add_materials_resume_parser(materials_subparsers.add_parser("resume", help="Resume a paused generic materials research workflow."))
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
    parser.add_argument("--verbose", action="store_true", help="Print verbose streamed node updates.")
    parser.add_argument("--overwrite", action="store_true", help="Allow overwriting generated workspaces.")
    parser.add_argument("--approve", action="store_true", help="Approve a full-run execution request.")
    parser.set_defaults(allow_full_run=False, use_llm=False)


def _add_materials_run_parser(parser: argparse.ArgumentParser) -> None:
    _add_run_parser(parser)
    parser.add_argument(
        "--user-file",
        action="append",
        default=[],
        help="Attach a user-provided local file for the generic materials research graph.",
    )
    parser.add_argument(
        "--literature-file",
        action="append",
        default=[],
        help="Attach a local literature note/text/pdf file for the generic materials research graph.",
    )
    parser.add_argument(
        "--experimental-file",
        action="append",
        default=[],
        help="Attach an experimental dataset file for the generic materials research graph.",
    )
    parser.add_argument(
        "--source-list-file",
        action="append",
        default=[],
        help="Attach a text file containing DOI, URL, or arXiv ids, one per line.",
    )
    parser.add_argument(
        "--literature-source",
        action="append",
        default=[],
        help="Attach a literature source note, DOI, URL, or bibliography string.",
    )


def _add_materials_resume_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--thread-id", required=True, help="Thread id of the paused materials research workflow.")
    parser.add_argument("--verbose", action="store_true", help="Print verbose streamed node updates.")
    parser.add_argument(
        "--decision",
        default="approve",
        help="Human review decision to resume with, for example approve, reject, correction, or annotation.",
    )
    parser.add_argument("--comments", default=None, help="Optional human review comments.")
    parser.add_argument("--route-hint", default=None, help="Optional routing hint such as revise_parameters.")
    parser.add_argument(
        "--state-patch",
        default=None,
        help="Optional JSON object patch to merge into the paused state before resuming.",
    )


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

    if args.command == "materials" and args.materials_command == "run":
        if args.approve and not args.allow_full_run:
            parser.error("--approve can only be used together with --full-run.")
        mode = _resolve_mode(args)
        final_state = run_materials_research_graph(
            user_query=args.query,
            mode=mode,
            use_llm=args.use_llm,
            model=args.model_name,
            max_iterations=args.max_iterations,
            user_files=args.user_file,
            literature_files=args.literature_file,
            experimental_files=args.experimental_file,
            literature_sources=args.literature_source,
            source_list_files=args.source_list_file,
            user_constraints={
                "approve": args.approve,
                "allow_overwrite": args.overwrite,
            },
            checkpoint=True,
            thread_id=args.thread_id,
            stream=True,
            verbose=args.verbose,
        )
        if "__interrupt__" in final_state:
            print(f"Materials research graph paused for human review. Thread: {final_state.get('__thread_id__', args.thread_id or '<generated>')}")
            print(_format_interrupt_summary(final_state["__interrupt__"], verbose=args.verbose))
            return 0
        report_path = final_state.get("report_path") or str(Path("workspaces") / "materials_research_report.md")
        print(f"Completed materials research pipeline. Report: {report_path}")
        return 0

    if args.command == "materials" and args.materials_command == "resume":
        state_patch = json.loads(args.state_patch) if args.state_patch else None
        final_state = resume_materials_research_graph(
            thread_id=args.thread_id,
            decision=args.decision,
            comments=args.comments,
            route_hint=args.route_hint,
            state_patch=state_patch,
            checkpoint=True,
            stream=True,
            verbose=args.verbose,
        )
        if "__interrupt__" in final_state:
            print(f"Materials research graph paused for human review. Thread: {final_state.get('__thread_id__', args.thread_id)}")
            print(_format_interrupt_summary(final_state["__interrupt__"], verbose=args.verbose))
            return 0
        report_path = final_state.get("report_path") or str(Path("workspaces") / "materials_research_report.md")
        print(f"Resumed materials research pipeline. Report: {report_path}")
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


def _format_interrupt_summary(interrupt_payload, *, verbose: bool = False) -> str:
    if verbose:
        return f"Interrupt: {interrupt_payload}"

    entries = interrupt_payload if isinstance(interrupt_payload, list) else [interrupt_payload]
    if not entries:
        return "Interrupt: review requested."

    first = entries[0]
    value = getattr(first, "value", None)
    if not isinstance(value, dict):
        return "Interrupt: review requested."

    stage = value.get("stage", "unknown")
    review_type = value.get("review_type", "unknown")
    material = dict(value.get("research_case") or {}).get("material_system", "unknown")
    return (
        f"Interrupt: stage={stage}, review_type={review_type}, material={material}. "
        "Use `damask-copilot materials resume --thread-id ... --decision approve` to continue."
    )


if __name__ == "__main__":
    raise SystemExit(main())

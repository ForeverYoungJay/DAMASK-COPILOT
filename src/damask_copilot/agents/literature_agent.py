"""Literature-style background agent."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from damask_copilot.graph.state import DamaskResearchState, append_trace
from damask_copilot.llm.prompts import load_prompt
from damask_copilot.llm.structured_runner import StructuredLLMRunner
from damask_copilot.mcp_clients.literature_mcp_client import LiteratureMCPClient
from damask_copilot.schemas.llm_outputs import LiteratureAgentOutput


class LiteratureAgent:
    """Search, access, and synthesize literature evidence for planning."""

    name = "literature_agent"

    def __init__(
        self,
        *,
        use_llm: bool = False,
        model_name: str | None = None,
        llm_runner: StructuredLLMRunner | None = None,
        literature_client: LiteratureMCPClient | None = None,
    ) -> None:
        self.use_llm = use_llm
        self.model_name = model_name
        self.llm_runner = llm_runner
        self.literature_client = literature_client or LiteratureMCPClient()

    def run(self, state: DamaskResearchState) -> DamaskResearchState:
        auto_search = self._search_related_literature(state)
        user_sources = self._retrieve_user_supplied_literature(state)
        external = self._merge_external_results(auto_search, user_sources)
        local_source_files = self._resolve_local_source_files(state)
        archived = self._archive_external_evidence(state, external)
        external = self._merge_external_and_local(external, archived)
        local = self._read_local_literature_files(
            state,
            extra_files=local_source_files + list(archived.get("local_files", [])),
        )
        merged = self._merge_external_and_local(external, local)
        if self.use_llm or state.get("use_llm", False):
            return self._run_llm(state, merged)
        return self._run_deterministic(state, merged)

    def _run_llm(self, state: DamaskResearchState, external: dict[str, Any]) -> DamaskResearchState:
        runner = self.llm_runner or StructuredLLMRunner(model_name=state.get("model") or self.model_name)
        parsed = runner.run_structured(
            prompt_name="literature_agent",
            system_prompt=load_prompt("literature_agent"),
            user_prompt=(
                f"User query: {state['user_query']}\n"
                f"Research goal: {state.get('research_goal')}\n"
                f"Mode: {state.get('mode')}\n"
                f"Literature sources: {state.get('literature_sources', [])}\n"
                f"External literature evidence summary: {external.get('summary', '')}\n"
                f"External evidence items: {self._compact_external_evidence(external)}"
            ),
            output_schema=LiteratureAgentOutput,
            model_name=state.get("model") or self.model_name,
        )
        updated = dict(state)
        updated["literature_external_results"] = external
        updated["literature_analysis"] = parsed.model_dump()
        notes = self._merge_literature_notes(parsed, external)
        updated["literature_notes"] = notes
        return append_trace(updated, self.name, "literature_notes_llm", {
            "literature_analysis": parsed.model_dump(),
            "providers_succeeded": external.get("providers_succeeded", []),
        })

    def _run_deterministic(self, state: DamaskResearchState, external: dict[str, Any]) -> DamaskResearchState:
        analysis = self._build_deterministic_analysis(state, external)
        notes = self._merge_literature_notes(analysis, external)
        updated = dict(state)
        updated["literature_external_results"] = external
        updated["literature_analysis"] = analysis
        updated["literature_notes"] = notes
        return append_trace(updated, self.name, "literature_notes_added", {
            "count": len(notes),
            "planning_implication_count": len(analysis.get("planning_implications", [])),
            "providers_succeeded": external.get("providers_succeeded", []),
        })

    def _search_related_literature(self, state: DamaskResearchState) -> dict[str, Any]:
        try:
            if hasattr(self.literature_client, "search_related_literature"):
                result = self.literature_client.search_related_literature(user_query=state["user_query"])
            else:
                result = self.literature_client.collect_literature(
                    user_query=state["user_query"],
                    literature_sources=[],
                )
            return self._with_stage_metadata(
                result,
                stage="auto_search",
                summary_prefix="Automatic MCP literature search",
            )
        except Exception as exc:
            return self._failed_external_stage(
                stage="auto_search",
                summary="Automatic MCP literature search failed.",
                exc=exc,
            )

    def _retrieve_user_supplied_literature(self, state: DamaskResearchState) -> dict[str, Any]:
        sources = self._non_file_literature_sources(state)
        if not sources:
            return self._with_stage_metadata(
                {
                    "used_external_retrieval": False,
                    "providers_attempted": [],
                    "providers_succeeded": [],
                    "notes": [],
                    "summary": "No user DOI, arXiv ID, or URL was supplied.",
                    "evidence_items": [],
                    "resolved_sources": [],
                    "uncertainties": [],
                },
                stage="user_sources",
                summary_prefix="User-supplied literature retrieval",
            )
        try:
            if hasattr(self.literature_client, "collect_from_sources"):
                result = self.literature_client.collect_from_sources(
                    user_query=state["user_query"],
                    literature_sources=sources,
                )
            else:
                result = self.literature_client.collect_literature(
                    user_query=state["user_query"],
                    literature_sources=sources,
                )
            return self._with_stage_metadata(
                result,
                stage="user_sources",
                summary_prefix="User-supplied literature retrieval",
            )
        except Exception as exc:
            return self._failed_external_stage(
                stage="user_sources",
                summary="User-supplied literature retrieval failed.",
                exc=exc,
            )

    def _read_local_literature_files(
        self,
        state: DamaskResearchState,
        *,
        extra_files: list[str] | None = None,
    ) -> dict[str, Any]:
        notes: list[str] = []
        resolved_files: list[str] = []
        uncertainties: list[str] = []
        candidate_files = list(state.get("literature_files", []))
        for file_path in extra_files or []:
            if file_path not in candidate_files:
                candidate_files.append(file_path)
        for file_path in candidate_files:
            path = Path(file_path)
            if not path.exists():
                uncertainties.append(f"Missing literature file: {file_path}")
                continue
            resolved_files.append(str(path))
            try:
                text = self._extract_local_literature_text(path)
            except Exception as exc:
                uncertainties.append(f"{path.name}: {type(exc).__name__}: {exc}")
                continue
            if text:
                notes.append(f"Local literature file {path.name}: {text[:20000]}")
        return {
            "used_local_files": bool(resolved_files),
            "local_files": resolved_files,
            "notes": notes,
            "uncertainties": uncertainties,
        }

    def _resolve_local_source_files(self, state: DamaskResearchState) -> list[str]:
        resolved: list[str] = []
        for source in list(state.get("literature_sources", [])):
            path = self._source_to_local_path(source)
            if path is None:
                continue
            normalized = str(path)
            if normalized not in resolved:
                resolved.append(normalized)
        return resolved

    def _non_file_literature_sources(self, state: DamaskResearchState) -> list[Any]:
        filtered: list[Any] = []
        for source in list(state.get("literature_sources", [])):
            if self._source_to_local_path(source) is not None:
                continue
            filtered.append(source)
        return filtered

    def _source_to_local_path(self, source: Any) -> Path | None:
        if isinstance(source, dict):
            for key in ("path", "file", "filepath"):
                value = source.get(key)
                if value:
                    candidate = Path(str(value))
                    if candidate.exists():
                        return candidate
            return None
        if not isinstance(source, str):
            return None
        candidate = Path(source)
        return candidate if candidate.exists() else None

    def _merge_external_and_local(self, external: dict[str, Any], local: dict[str, Any]) -> dict[str, Any]:
        merged = dict(external)
        notes = list(external.get("notes", []))
        for item in local.get("notes", []):
            if item not in notes:
                notes.append(item)
        merged["notes"] = notes
        uncertainties = list(external.get("uncertainties", []))
        for item in local.get("uncertainties", []):
            if item not in uncertainties:
                uncertainties.append(item)
        merged["uncertainties"] = uncertainties
        merged["local_files"] = list(local.get("local_files", []))
        merged["used_local_files"] = bool(local.get("used_local_files"))
        archive_dir = external.get("archive_dir") or local.get("archive_dir")
        if archive_dir:
            merged["archive_dir"] = archive_dir
        summary = external.get("summary", "")
        if local.get("used_local_files"):
            if summary and "Local literature files were also supplied." not in summary:
                summary = f"{summary} Local literature files were also supplied."
            else:
                summary = summary or "Local literature files were supplied for synthesis."
        merged["summary"] = summary
        return merged

    def _archive_external_evidence(self, state: DamaskResearchState, external: dict[str, Any]) -> dict[str, Any]:
        evidence_items = list(external.get("evidence_items", []))
        if not evidence_items:
            return {
                "used_local_files": False,
                "local_files": [],
                "notes": [],
                "uncertainties": [],
            }

        archive_dir = self._literature_archive_dir(state)
        archive_dir.mkdir(parents=True, exist_ok=True)

        local_files: list[str] = []
        uncertainties: list[str] = []
        for index, item in enumerate(evidence_items, start=1):
            try:
                archived_path = self._write_evidence_item_markdown(archive_dir, item, index=index)
            except Exception as exc:
                uncertainties.append(
                    f"Failed to archive literature evidence {index}: {type(exc).__name__}: {exc}"
                )
                continue
            local_files.append(str(archived_path))

        return {
            "used_local_files": bool(local_files),
            "local_files": local_files,
            "notes": [f"Archived literature retrieval output under {archive_dir}."],
            "uncertainties": uncertainties,
            "archive_dir": str(archive_dir),
        }

    def _literature_archive_dir(self, state: DamaskResearchState) -> Path:
        workspace = state.get("workspace")
        if workspace:
            return Path(str(workspace)) / "literature"
        slug = self._slugify(state.get("user_query", "") or "literature")
        return Path("workspaces/.damask_copilot/literature_cache") / slug

    def _write_evidence_item_markdown(self, archive_dir: Path, item: dict[str, Any], *, index: int) -> Path:
        provider = str(item.get("provider") or "provider")
        tool = str(item.get("tool") or "tool")
        resolved_source = str(item.get("resolved_source") or f"item_{index}")
        safe_name = self._slugify(f"{index:02d}_{provider}_{tool}_{resolved_source}")[:120]
        path = archive_dir / f"{safe_name}.md"
        body = str(item.get("text") or "").strip()
        lines = [
            "# Retrieved Literature Evidence",
            "",
            f"- Provider: {provider}",
            f"- Tool: {tool}",
            f"- Resolved source: {resolved_source}",
            "",
            "## Full Retrieved Text",
            "",
            body or "No retrievable text was returned.",
            "",
        ]
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    @staticmethod
    def _slugify(value: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()
        return cleaned or "literature"

    def _merge_external_results(self, auto_search: dict[str, Any], user_sources: dict[str, Any]) -> dict[str, Any]:
        merged_notes: list[str] = []
        merged_evidence: list[dict[str, Any]] = []
        merged_uncertainties: list[str] = []
        merged_resolved_sources: list[str] = []
        providers_attempted: list[str] = []
        providers_succeeded: list[str] = []

        for payload in (auto_search, user_sources):
            for item in payload.get("notes", []):
                if item and item not in merged_notes:
                    merged_notes.append(item)
            for item in payload.get("evidence_items", []):
                if item and item not in merged_evidence:
                    merged_evidence.append(item)
            for item in payload.get("uncertainties", []):
                if item and item not in merged_uncertainties:
                    merged_uncertainties.append(item)
            for item in payload.get("resolved_sources", []):
                if item and item not in merged_resolved_sources:
                    merged_resolved_sources.append(item)
            for item in payload.get("providers_attempted", []):
                if item and item not in providers_attempted:
                    providers_attempted.append(item)
            for item in payload.get("providers_succeeded", []):
                if item and item not in providers_succeeded:
                    providers_succeeded.append(item)

        stages = [dict(item) for item in auto_search.get("retrieval_stages", [])]
        for item in user_sources.get("retrieval_stages", []):
            if item not in stages:
                stages.append(dict(item))

        summary_parts = [item.get("summary", "") for item in stages if item.get("summary")]
        return {
            "used_external_retrieval": bool(providers_succeeded),
            "providers_attempted": providers_attempted,
            "providers_succeeded": providers_succeeded,
            "notes": merged_notes,
            "summary": " ".join(summary_parts).strip()
            or "No external literature MCP provider returned usable evidence.",
            "evidence_items": merged_evidence,
            "resolved_sources": merged_resolved_sources,
            "uncertainties": merged_uncertainties,
            "retrieval_stages": stages,
        }

    def _with_stage_metadata(self, payload: dict[str, Any], *, stage: str, summary_prefix: str) -> dict[str, Any]:
        result = dict(payload)
        stage_summary = result.get("summary") or f"{summary_prefix} produced no summary."
        result["retrieval_stages"] = [
            {
                "stage": stage,
                "summary": stage_summary,
                "used_external_retrieval": bool(result.get("used_external_retrieval")),
                "providers_succeeded": list(result.get("providers_succeeded", [])),
                "resolved_sources": list(result.get("resolved_sources", [])),
            }
        ]
        return result

    def _failed_external_stage(self, *, stage: str, summary: str, exc: Exception) -> dict[str, Any]:
        return self._with_stage_metadata(
            {
                "used_external_retrieval": False,
                "providers_attempted": [],
                "providers_succeeded": [],
                "notes": [],
                "summary": summary,
                "evidence_items": [],
                "resolved_sources": [],
                "uncertainties": [f"{type(exc).__name__}: {exc}"],
            },
            stage=stage,
            summary_prefix=summary,
        )

    def _build_deterministic_analysis(self, state: DamaskResearchState, external: dict[str, Any]) -> dict[str, Any]:
        notes = [str(item) for item in external.get("notes", []) if item]
        text_blob = "\n".join(notes + [state.get("user_query", "")])
        lowered = text_blob.lower()

        mechanisms: list[str] = []
        if "slip" in lowered:
            mechanisms.append("slip-mediated plasticity")
        if "twinning" in lowered:
            mechanisms.append("twinning")
        if "hardening" in lowered:
            mechanisms.append("strain hardening")
        if "texture" in lowered or "orientation" in lowered:
            mechanisms.append("texture evolution")

        models: list[str] = []
        if "phenopowerlaw" in lowered:
            models.append("phenopowerlaw crystal plasticity")
        if "crystal plasticity" in lowered or "slip" in lowered:
            models.append("slip-based crystal plasticity")
        if "twinning" in lowered:
            models.append("crystal plasticity with twinning-capable kinematics")

        observables: list[str] = []
        if "stress" in lowered and "strain" in lowered:
            observables.append("stress_strain_curve")
        else:
            if "stress" in lowered:
                observables.append("stress")
            if "strain" in lowered:
                observables.append("strain")
        if "texture" in lowered or "orientation" in lowered:
            observables.append("texture_evolution")
        if "slip" in lowered:
            observables.append("slip_activity_proxy")

        experimental_conditions: list[str] = []
        if "tension" in lowered:
            experimental_conditions.append("uniaxial_tension")
        if "compression" in lowered:
            experimental_conditions.append("uniaxial_compression")
        if "shear" in lowered:
            experimental_conditions.append("simple_shear")
        if "cyclic" in lowered:
            experimental_conditions.append("cyclic_loading")
        if "temperature" in lowered:
            experimental_conditions.append("temperature_condition_reported")
        if "strain rate" in lowered or "strain-rate" in lowered or "rate sensitivity" in lowered:
            experimental_conditions.append("strain_rate_sensitive")

        planning_implications: list[str] = []
        if any("slip" in item for item in mechanisms):
            planning_implications.append("Choose a crystal-plasticity formulation that can represent FCC slip-driven deformation.")
        if "stress_strain_curve" in observables:
            planning_implications.append("Include volume-averaged stress-strain outputs to test the primary literature observable.")
        if "texture_evolution" in observables:
            planning_implications.append("Track orientation or texture-related outputs if the study aims to compare microstructural evolution.")
        if not planning_implications:
            planning_implications.append("Use literature only as qualitative framing and keep the first simulation plan conservative.")

        evidence_gaps: list[str] = []
        if not notes:
            evidence_gaps.append("No external literature evidence was available to ground the study design.")
        if "stress_strain_curve" not in observables:
            evidence_gaps.append("The retrieved evidence does not clearly define a primary validation observable.")
        if not models:
            evidence_gaps.append("The retrieved evidence does not clearly support a constitutive-model choice.")

        unsupported_claims: list[str] = []
        if not external.get("used_external_retrieval"):
            unsupported_claims.append("No externally retrieved article content is available; literature-based claims remain unverified.")
        if external.get("uncertainties"):
            unsupported_claims.append("Some provider calls failed or returned incomplete evidence; article coverage may be incomplete.")

        summary = external.get("summary") or (
            "Literature evidence was reviewed to guide hypothesis generation and conservative simulation planning."
            if notes
            else "No literature evidence was available; proceed with conservative planning assumptions only."
        )
        literature_notes = list(notes[:4])
        if not literature_notes:
            literature_notes = [
                "No external literature retrieval was performed in this run.",
                "Use conservative DAMASK smoke-test settings before making physical claims.",
            ]

        return {
            "summary": summary,
            "literature_notes": literature_notes,
            "relevant_mechanisms": mechanisms,
            "candidate_constitutive_models": models,
            "experimental_conditions": experimental_conditions,
            "observables_for_validation": observables,
            "planning_implications": planning_implications,
            "unsupported_claims": unsupported_claims,
            "evidence_gaps": evidence_gaps,
        }

    def _merge_literature_notes(self, analysis: LiteratureAgentOutput | dict[str, Any], external: dict[str, Any]) -> list[str]:
        if hasattr(analysis, "model_dump"):
            payload = analysis.model_dump()
        else:
            payload = dict(analysis)
        merged: list[str] = []
        for item in payload.get("literature_notes", []):
            if item and item not in merged:
                merged.append(str(item))
        for item in payload.get("planning_implications", []):
            entry = f"Planning implication: {item}"
            if item and entry not in merged:
                merged.append(entry)
        for item in payload.get("evidence_gaps", []):
            entry = f"Evidence gap: {item}"
            if item and entry not in merged:
                merged.append(entry)
        for item in external.get("uncertainties", []):
            entry = f"Literature retrieval uncertainty: {item}"
            if entry not in merged:
                merged.append(entry)
        for item in external.get("local_files", []):
            entry = f"Local literature file: {item}"
            if entry not in merged:
                merged.append(entry)
        return merged

    def _compact_external_evidence(self, external: dict[str, Any]) -> str:
        compact_items: list[dict[str, Any]] = []
        for item in list(external.get("evidence_items", []))[:6]:
            compact_items.append(
                {
                    "provider": item.get("provider"),
                    "tool": item.get("tool"),
                    "resolved_source": item.get("resolved_source"),
                    "text": str(item.get("text", ""))[:800],
                }
            )
        return json.dumps(compact_items, ensure_ascii=False)

    def _extract_local_literature_text(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix in {".md", ".txt", ".bib", ".ris", ".yaml", ".yml", ".json"}:
            return path.read_text(encoding="utf-8")
        if suffix == ".pdf":
            try:
                from pypdf import PdfReader
            except Exception:
                return f"PDF file available at {path}. Text extraction library is not installed."
            reader = PdfReader(str(path))
            texts: list[str] = []
            total_chars = 0
            for page in reader.pages:
                page_text = page.extract_text() or ""
                if not page_text:
                    continue
                texts.append(page_text)
                total_chars += len(page_text)
                if total_chars >= 40000:
                    break
            return "\n".join(texts).strip() or f"PDF file available at {path}, but no extractable text was found."
        return f"Local literature file available at {path}."

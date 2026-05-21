"""External literature MCP client wrappers."""

from __future__ import annotations

import json
import os
import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import anyio
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

DOI_PATTERN = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
ARXIV_PATTERN = re.compile(r"(?:arxiv:)?(\d{4}\.\d{4,5}(?:v\d+)?)", re.IGNORECASE)


@dataclass
class LiteratureMCPProviderConfig:
    """Configuration for one external literature MCP provider."""

    name: str
    command: str
    args: list[str]
    env: dict[str, str]
    cwd: str | None = None
    enabled: bool = True


class LiteratureMCPClient:
    """Query external literature MCP servers over stdio."""

    def __init__(
        self,
        providers: list[LiteratureMCPProviderConfig] | None = None,
        *,
        max_results: int = 5,
        auto_search: bool | None = None,
    ) -> None:
        self.providers = providers or self.default_providers()
        self.max_results = max_results
        self.auto_search = (
            os.getenv("DAMASK_COPILOT_LITERATURE_AUTO_SEARCH", "1").lower() in {"1", "true", "yes", "on"}
            if auto_search is None
            else auto_search
        )

    @classmethod
    def default_providers(cls) -> list[LiteratureMCPProviderConfig]:
        """Build the default provider list from documented MCP servers and environment overrides."""
        return [
            cls._provider_from_env(
                name="semantic_scholar",
                default_command="uvx",
                default_args=[
                    "--from",
                    "git+https://github.com/akapet00/semantic-scholar-mcp",
                    "semantic-scholar-mcp",
                ],
                pass_env=["SEMANTIC_SCHOLAR_API_KEY", "DISABLE_SSL_VERIFY"],
            ),
            cls._provider_from_env(
                name="elsevier",
                default_command="npx",
                default_args=["-y", "elsevier-mcp"],
                pass_env=["ELSEVIER_API_KEY", "ELSEVIER_INST_TOKEN", "ELSEVIER_ENABLE_ALL_TOOLS"],
            ),
            cls._provider_from_env(
                name="arxiv",
                default_command="uvx",
                default_args=[
                    "arxiv-mcp-server",
                    "--storage-path",
                    str(Path("workspaces/.damask_copilot/arxiv_papers")),
                ],
                pass_env=["TRANSPORT", "HOST", "PORT", "ALLOWED_HOSTS", "ALLOWED_ORIGINS"],
            ),
        ]

    @classmethod
    def _provider_from_env(
        cls,
        *,
        name: str,
        default_command: str,
        default_args: list[str],
        pass_env: list[str],
    ) -> LiteratureMCPProviderConfig:
        prefix = f"DAMASK_COPILOT_{name.upper()}_MCP"
        enabled_raw = os.getenv(f"{prefix}_ENABLED", "true").lower()
        enabled = enabled_raw not in {"0", "false", "no", "off"}
        command = os.getenv(f"{prefix}_COMMAND", default_command)
        args_raw = os.getenv(f"{prefix}_ARGS")
        args = shlex.split(args_raw) if args_raw else list(default_args)
        env = {key: value for key in pass_env if (value := os.getenv(key)) is not None}
        extra_env_raw = os.getenv(f"{prefix}_ENV_JSON")
        if extra_env_raw:
            env.update(json.loads(extra_env_raw))
        cwd = os.getenv(f"{prefix}_CWD")
        return LiteratureMCPProviderConfig(name=name, command=command, args=args, env=env, cwd=cwd, enabled=enabled)

    def collect_literature(
        self,
        *,
        user_query: str,
        literature_sources: list[Any] | None = None,
    ) -> dict[str, Any]:
        """Query enabled providers and aggregate literature evidence."""
        resolved_sources = list(literature_sources or [])
        if not resolved_sources and not self.auto_search:
            return {
                "used_external_retrieval": False,
                "providers_attempted": [],
                "providers_succeeded": [],
                "notes": [],
                "summary": "External literature retrieval was skipped because no literature sources were supplied.",
                "evidence_items": [],
                "resolved_sources": [],
                "uncertainties": [],
            }
        return anyio.run(self._collect_literature_async, user_query, resolved_sources)

    def search_related_literature(self, *, user_query: str) -> dict[str, Any]:
        """Search related literature from the query alone."""
        if not self.auto_search:
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
        return anyio.run(self._collect_literature_async, user_query, [])

    def collect_from_sources(
        self,
        *,
        user_query: str,
        literature_sources: list[Any] | None = None,
    ) -> dict[str, Any]:
        """Retrieve literature evidence directly from user-supplied identifiers."""
        resolved_sources = list(literature_sources or [])
        if not resolved_sources:
            return {
                "used_external_retrieval": False,
                "providers_attempted": [],
                "providers_succeeded": [],
                "notes": [],
                "summary": "No user-supplied literature identifiers were provided.",
                "evidence_items": [],
                "resolved_sources": [],
                "uncertainties": [],
            }
        return anyio.run(self._collect_literature_async, user_query, resolved_sources)

    async def _collect_literature_async(self, user_query: str, literature_sources: list[Any]) -> dict[str, Any]:
        providers_attempted: list[str] = []
        providers_succeeded: list[str] = []
        notes: list[str] = []
        evidence_items: list[dict[str, Any]] = []
        errors: list[str] = []

        for provider in self.providers:
            if not provider.enabled:
                continue
            providers_attempted.append(provider.name)
            try:
                provider_items = await self._query_provider(provider, user_query=user_query, literature_sources=literature_sources)
            except Exception as exc:
                errors.append(f"{provider.name}: {type(exc).__name__}: {exc}")
                continue
            provider_items = [item for item in provider_items if self._is_usable_evidence_text(str(item.get("text") or ""))]
            if provider_items:
                providers_succeeded.append(provider.name)
                evidence_items.extend(provider_items)

        for item in evidence_items:
            text = item.get("text")
            if text and text not in notes:
                notes.append(text)

        summary = (
            f"External literature retrieval used {len(providers_succeeded)} provider(s): {', '.join(providers_succeeded)}."
            if providers_succeeded
            else "No external literature MCP provider returned usable evidence."
        )

        return {
            "used_external_retrieval": bool(providers_succeeded),
            "providers_attempted": providers_attempted,
            "providers_succeeded": providers_succeeded,
            "notes": notes,
            "summary": summary,
            "evidence_items": evidence_items,
            "resolved_sources": self._resolved_sources_from_items(evidence_items),
            "uncertainties": errors,
        }

    async def _query_provider(
        self,
        provider: LiteratureMCPProviderConfig,
        *,
        user_query: str,
        literature_sources: list[Any],
    ) -> list[dict[str, Any]]:
        server = StdioServerParameters(
            command=provider.command,
            args=provider.args,
            env=provider.env or None,
            cwd=provider.cwd,
        )
        async with stdio_client(server) as (read_stream, write_stream):
            session = ClientSession(read_stream, write_stream)
            async with session:
                await session.initialize()
                tools_result = await session.list_tools()
                tool_names = {tool.name for tool in getattr(tools_result, "tools", [])}
                return await self._query_with_session(
                    session,
                    provider.name,
                    tool_names,
                    user_query=user_query,
                    literature_sources=literature_sources,
                )

    async def _query_with_session(
        self,
        session: ClientSession,
        provider_name: str,
        tool_names: set[str],
        *,
        user_query: str,
        literature_sources: list[Any],
    ) -> list[dict[str, Any]]:
        if provider_name == "semantic_scholar":
            return await self._query_semantic_scholar(session, tool_names, user_query, literature_sources)
        if provider_name == "elsevier":
            return await self._query_elsevier(session, tool_names, user_query, literature_sources)
        if provider_name == "arxiv":
            return await self._query_arxiv(session, tool_names, user_query, literature_sources)
        return []

    async def _query_semantic_scholar(
        self,
        session: ClientSession,
        tool_names: set[str],
        user_query: str,
        literature_sources: list[Any],
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        related_identifiers: list[str] = []
        if "get_paper_details" in tool_names:
            for source in literature_sources:
                source_text = self._normalize_source(source)
                doi = self._extract_doi(source_text)
                arxiv_id = self._extract_arxiv_id(source_text)
                identifier = f"DOI:{doi}" if doi else (f"ARXIV:{arxiv_id}" if arxiv_id else None)
                if not identifier:
                    continue
                result = await session.call_tool("get_paper_details", {"paper_id": identifier})
                text = self._tool_result_text(result)
                if text:
                    items.append(self._make_item("semantic_scholar", "get_paper_details", identifier, text))
                    related_identifiers.extend(self._extract_semantic_scholar_identifiers(text))
        if "search_papers" in tool_names:
            result = await self._call_tool_with_fallbacks(
                session,
                "search_papers",
                [
                    {"query": user_query, "max_results": self.max_results},
                    {"query": user_query, "limit": self.max_results},
                    {"query": user_query},
                ],
            )
            text = self._tool_result_text(result)
            if text:
                items.append(self._make_item("semantic_scholar", "search_papers", user_query, text))
                related_identifiers.extend(self._extract_semantic_scholar_identifiers(text))
        if "get_paper_details" in tool_names:
            for identifier in self._unique_preserve_order(related_identifiers)[: max(1, self.max_results)]:
                if any(item["resolved_source"] == identifier and item["tool"] == "get_paper_details" for item in items):
                    continue
                result = await session.call_tool("get_paper_details", {"paper_id": identifier})
                text = self._tool_result_text(result)
                if text:
                    items.append(self._make_item("semantic_scholar", "get_paper_details", identifier, text))
        if "get_paper_references" in tool_names:
            source_id = next(
                (
                    item["resolved_source"]
                    for item in items
                    if self._looks_like_structured_source_reference(str(item.get("resolved_source") or ""))
                ),
                None,
            )
            if source_id is None:
                return items
            result = await session.call_tool("get_paper_references", {"paper_id": source_id})
            text = self._tool_result_text(result)
            if text:
                items.append(self._make_item("semantic_scholar", "get_paper_references", source_id, text))
        return items

    async def _query_elsevier(
        self,
        session: ClientSession,
        tool_names: set[str],
        user_query: str,
        literature_sources: list[Any],
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        related_dois: list[str] = []
        if "abstract_retrieval" in tool_names:
            for source in literature_sources:
                source_text = self._normalize_source(source)
                doi = self._extract_doi(source_text)
                if not doi:
                    continue
                result = await session.call_tool("abstract_retrieval", {"identifier": doi})
                text = self._tool_result_text(result)
                if text:
                    items.append(self._make_item("elsevier", "abstract_retrieval", doi, text))
                    related_dois.extend(self._extract_dois(text))
        if "scopus_search" in tool_names:
            result = await session.call_tool("scopus_search", {"query": user_query})
            text = self._tool_result_text(result)
            if text:
                items.append(self._make_item("elsevier", "scopus_search", user_query, text))
                related_dois.extend(self._extract_dois(text))
        for doi in self._unique_preserve_order(related_dois)[: max(1, self.max_results)]:
            if "abstract_retrieval" in tool_names and not any(item["resolved_source"] == doi and item["tool"] == "abstract_retrieval" for item in items):
                result = await session.call_tool("abstract_retrieval", {"identifier": doi})
                text = self._tool_result_text(result)
                if text:
                    items.append(self._make_item("elsevier", "abstract_retrieval", doi, text))
        if "article_retrieval" in tool_names:
            article_targets = []
            for source in literature_sources:
                source_text = self._normalize_source(source)
                doi = self._extract_doi(source_text)
                if doi:
                    article_targets.append(doi)
            article_targets.extend(self._unique_preserve_order(related_dois))
            for doi in self._unique_preserve_order(article_targets)[: max(1, self.max_results)]:
                result = await session.call_tool("article_retrieval", {"identifier": doi})
                text = self._tool_result_text(result)
                if text:
                    items.append(self._make_item("elsevier", "article_retrieval", doi, text))
        return items

    async def _query_arxiv(
        self,
        session: ClientSession,
        tool_names: set[str],
        user_query: str,
        literature_sources: list[Any],
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        paper_ids: list[str] = []
        if "search_papers" in tool_names:
            result = await self._call_tool_with_fallbacks(
                session,
                "search_papers",
                [
                    {"query": user_query, "max_results": self.max_results},
                    {"query": user_query, "limit": self.max_results},
                    {"query": user_query},
                ],
            )
            text = self._tool_result_text(result)
            if text:
                items.append(self._make_item("arxiv", "search_papers", user_query, text))
                paper_ids.extend(self._extract_arxiv_ids(text))
        if "download_paper" in tool_names and "read_paper" in tool_names:
            for source in literature_sources:
                source_text = self._normalize_source(source)
                paper_id = self._extract_arxiv_id(source_text)
                if not paper_id:
                    continue
                paper_ids.append(paper_id)
            for paper_id in self._unique_preserve_order(paper_ids)[: max(1, self.max_results)]:
                await session.call_tool("download_paper", {"paper_id": paper_id, "max_chars": 20000})
                result = await session.call_tool("read_paper", {"paper_id": paper_id, "max_chars": 20000})
                text = self._tool_result_text(result)
                if text:
                    items.append(self._make_item("arxiv", "read_paper", paper_id, text))
        return items

    @staticmethod
    def _normalize_source(source: Any) -> str:
        if isinstance(source, dict):
            for key in ("doi", "url", "title", "citation", "text"):
                value = source.get(key)
                if value:
                    return str(value)
            return json.dumps(source, ensure_ascii=False)
        return str(source)

    @staticmethod
    def _extract_doi(text: str) -> str | None:
        match = DOI_PATTERN.search(text)
        return match.group(0) if match else None

    @staticmethod
    def _extract_dois(text: str) -> list[str]:
        return [match.group(0) for match in DOI_PATTERN.finditer(text)]

    @staticmethod
    def _extract_arxiv_id(text: str) -> str | None:
        match = ARXIV_PATTERN.search(text)
        return match.group(1) if match else None

    @staticmethod
    def _extract_arxiv_ids(text: str) -> list[str]:
        return [match.group(1) for match in ARXIV_PATTERN.finditer(text)]

    @classmethod
    def _extract_semantic_scholar_identifiers(cls, text: str) -> list[str]:
        identifiers: list[str] = []
        for doi in cls._extract_dois(text):
            identifiers.append(f"DOI:{doi}")
        for arxiv_id in cls._extract_arxiv_ids(text):
            identifiers.append(f"ARXIV:{arxiv_id}")
        return identifiers

    @staticmethod
    def _tool_result_text(result: Any) -> str:
        structured = getattr(result, "structuredContent", None)
        if structured:
            return json.dumps(structured, ensure_ascii=False)
        parts: list[str] = []
        for item in getattr(result, "content", []):
            text = getattr(item, "text", None)
            if text:
                parts.append(text)
        return "\n".join(parts)

    @staticmethod
    def _make_item(provider: str, tool: str, resolved_source: str, text: str) -> dict[str, Any]:
        return {
            "provider": provider,
            "tool": tool,
            "resolved_source": resolved_source,
            "text": text[:20000],
        }

    @staticmethod
    async def _call_tool_with_fallbacks(session: ClientSession, tool_name: str, attempts: list[dict[str, Any]]) -> Any:
        last_error: Exception | None = None
        for payload in attempts:
            try:
                return await session.call_tool(tool_name, payload)
            except Exception as exc:
                last_error = exc
                message = str(exc).lower()
                if "unexpected keyword" not in message and "validation error" not in message:
                    raise
        if last_error is not None:
            raise last_error
        raise RuntimeError(f"No payload attempts were provided for {tool_name}.")

    @classmethod
    def _resolved_sources_from_items(cls, items: list[dict[str, Any]]) -> list[str]:
        resolved: list[str] = []
        for item in items:
            source = cls._normalize_source_reference(str(item.get("resolved_source") or ""))
            if source and source not in resolved:
                resolved.append(source)
                continue
            for extracted in cls._extract_source_references_from_text(str(item.get("text") or "")):
                normalized = cls._normalize_source_reference(extracted)
                if normalized and normalized not in resolved:
                    resolved.append(normalized)
        return resolved

    @classmethod
    def _extract_source_references_from_text(cls, text: str) -> list[str]:
        refs: list[str] = []
        for doi in cls._extract_dois(text):
            refs.append(f"DOI:{doi}")
        for arxiv_id in cls._extract_arxiv_ids(text):
            refs.append(f"ARXIV:{arxiv_id}")
        return cls._unique_preserve_order(refs)

    @staticmethod
    def _is_usable_evidence_text(text: str) -> bool:
        lowered = text.lower().strip()
        if not lowered:
            return False
        failure_tokens = [
            "validation error for call",
            "unexpected keyword argument",
            "paper not found",
            "result set was empty",
            "rate limiting",
            "\"error\"",
            "error:",
        ]
        return not any(token in lowered for token in failure_tokens)

    @classmethod
    def _looks_like_structured_source_reference(cls, value: str) -> bool:
        return cls._normalize_source_reference(value) is not None

    @classmethod
    def _normalize_source_reference(cls, value: str) -> str | None:
        text = value.strip()
        if not text:
            return None
        doi = cls._extract_doi(text)
        if doi:
            return f"DOI:{doi}"
        arxiv_id = cls._extract_arxiv_id(text)
        if arxiv_id:
            return f"ARXIV:{arxiv_id}"
        if text.startswith(("http://", "https://")):
            return text
        if "/" in text and Path(text).suffix:
            return text
        return None

    @staticmethod
    def _unique_preserve_order(items: list[str]) -> list[str]:
        unique: list[str] = []
        seen: set[str] = set()
        for item in items:
            if item in seen:
                continue
            seen.add(item)
            unique.append(item)
        return unique

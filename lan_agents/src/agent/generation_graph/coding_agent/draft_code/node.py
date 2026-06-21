"""Coding Agent node that drafts a static HTML5 bundle."""

from __future__ import annotations

import json
import re
from collections import OrderedDict
from datetime import UTC, datetime
from typing import Any

from agent.generation_graph.state import GenerationState
from agent.generation_graph.tools.path_safety import ensure_workspace_root
from agent.generation_graph.tools.runtime_protocol import ensure_game_ready_signal
from agent.generation_graph.tools.workspace import write_workspace_text
from agent.providers import LLMMessage, LLMProvider, ProviderError, provider_from_env

CODING_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["index_html", "style_css", "game_js", "coding_notes"],
    "properties": {
        "index_html": {"type": "string"},
        "style_css": {"type": "string"},
        "game_js": {"type": "string"},
        "coding_notes": {"type": "array"},
    },
}

CODING_SYSTEM_PROMPT = """
You are the Coding Agent for Yahaha_Play.

Return one JSON object with exactly these keys:
- index_html
- style_css
- game_js
- coding_notes

Rules:
- produce a static HTML5 game only
- do not use React, external libraries, or remote CDN scripts/styles/assets
- the only local files you may reference are index.html, style.css, game.js, and asset paths already listed in asset_manifest_plan
- asset_manifest_plan may be empty; in that case draw background, player, and effects procedurally in game.js
- if an effect can be drawn procedurally, implement it in game.js instead of inventing new asset files
- do not include secrets, tokens, passwords, signed URLs, or absolute local paths
- keep the game runnable in a sandboxed iframe with allow-scripts only
- game_js must call window.parent.postMessage({ type: 'game_ready' }, '*') after initialization so Play can mark the iframe ready
- keep the output compact: no comments, no unnecessary whitespace, and concise gameplay logic
- every field value must remain valid JSON strings
- prefer single quotes inside HTML, CSS, and JS so the outer JSON stays valid more reliably
""".strip()

ASSET_REFERENCE_PATTERN = re.compile(r"assets/[A-Za-z0-9._/-]+")
REMOTE_REFERENCE_PATTERN = re.compile(r"(https?:)?//", re.IGNORECASE)
SECRET_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]+|X-Amz-Signature=|Authorization:|Bearer\s+[A-Za-z0-9._-]+)",
    re.IGNORECASE,
)
ABSOLUTE_PATH_PATTERN = re.compile(r"""(['"])\/(?!\/)[^'"]+\1|url\(\s*\/(?!\/)[^)]+\)""")


def draft_code(
    state: GenerationState, provider: LLMProvider | None = None
) -> dict[str, Any]:
    """Draft bundle files from a development brief and planned asset paths."""
    if not state.development_brief:
        raise ProviderError("Coding Agent requires development_brief")
    if not state.artifact_workspace:
        raise ProviderError("Coding Agent requires artifact_workspace")

    active_provider = provider or provider_from_env()
    llm_result = _complete_coding_bundle(active_provider, state)
    html = _require_text(llm_result.get("index_html"), "index_html")
    css = _require_text(llm_result.get("style_css"), "style_css")
    js = _require_text(llm_result.get("game_js"), "game_js")
    js = ensure_game_ready_signal(js)
    notes = _normalize_notes(llm_result.get("coding_notes"))

    _reject_unsafe_content(html, "index_html")
    _reject_unsafe_content(css, "style_css")
    _reject_unsafe_content(js, "game_js")

    referenced_assets = _collect_asset_references([html, css, js], state.asset_manifest_plan)
    manifest_draft = _build_manifest_draft(state, referenced_assets)

    workspace_root = ensure_workspace_root(state.artifact_workspace)
    index_html_path = write_workspace_text(workspace_root, "index.html", html)
    style_css_path = write_workspace_text(workspace_root, "style.css", css)
    game_js_path = write_workspace_text(workspace_root, "game.js", js)
    manifest_draft_path = write_workspace_text(
        workspace_root,
        "manifest_draft.json",
        json.dumps(manifest_draft, ensure_ascii=False, indent=2),
    )

    return {
        "code_artifacts": {
            "index_html_path": str(index_html_path),
            "style_css_path": str(style_css_path),
            "game_js_path": str(game_js_path),
            "manifest_draft_path": str(manifest_draft_path),
            "files": [
                _build_code_file_record("index.html", index_html_path),
                _build_code_file_record("style.css", style_css_path),
                _build_code_file_record("game.js", game_js_path),
                _build_code_file_record("manifest_draft.json", manifest_draft_path),
            ],
            "referenced_asset_paths": referenced_assets,
        },
        "manifest_draft": manifest_draft,
        "coding_notes": notes,
        "generation_status": "code_drafted",
    }


def _messages_from_state(state: GenerationState) -> list[LLMMessage]:
    payload = {
        "development_brief": state.development_brief,
        "asset_manifest_plan": state.asset_manifest_plan,
        "game_spec": state.game_spec,
        "game_plan": {
            "title": state.game_plan.get("title"),
            "introduction": state.game_plan.get("introduction"),
            "controls": state.game_plan.get("controls"),
        },
    }
    return [
        LLMMessage(role="system", content=CODING_SYSTEM_PROMPT),
        LLMMessage(role="user", content=json.dumps(payload, ensure_ascii=False)),
    ]


def _complete_coding_bundle(
    provider: LLMProvider,
    state: GenerationState,
) -> dict[str, Any]:
    last_error: ProviderError | None = None
    for _attempt in range(2):
        try:
            return provider.complete_json(
                messages=_messages_from_state(state),
                response_schema=CODING_RESPONSE_SCHEMA,
                temperature=0.0,
                max_tokens=5200,
            )
        except ProviderError as exc:
            if "invalid json" not in str(exc).lower():
                raise
            last_error = exc
    assert last_error is not None
    raise last_error


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProviderError(f"Coding Agent returned empty {field_name}")
    return value.strip()


def _normalize_notes(value: Any) -> list[str]:
    if isinstance(value, str):
        normalized = value.strip()
        return [normalized] if normalized else []
    if not isinstance(value, list):
        raise ProviderError("coding_notes must be a list or string")
    return [str(item).strip() for item in value if str(item).strip()]


def _reject_unsafe_content(content: str, field_name: str) -> None:
    if REMOTE_REFERENCE_PATTERN.search(content):
        raise ProviderError(f"Coding Agent generated remote or CDN reference in {field_name}")
    if SECRET_PATTERN.search(content):
        raise ProviderError(f"Coding Agent leaked secret-like content in {field_name}")
    if ABSOLUTE_PATH_PATTERN.search(content):
        raise ProviderError(f"Coding Agent used absolute local path in {field_name}")


def _collect_asset_references(
    contents: list[str], asset_manifest_plan: list[dict[str, Any]]
) -> list[str]:
    allowed = {str(item.get("target_path") or "").strip() for item in asset_manifest_plan}
    ordered: OrderedDict[str, None] = OrderedDict()
    for content in contents:
        for match in ASSET_REFERENCE_PATTERN.findall(content):
            if match not in allowed:
                raise ProviderError("Coding Agent referenced a path outside asset_manifest_plan")
            ordered.setdefault(match, None)
    return list(ordered.keys())


def _build_manifest_draft(state: GenerationState, referenced_assets: list[str]) -> dict[str, Any]:
    planned_cover = next(
        (
            str(item.get("target_path") or "").strip()
            for item in state.asset_manifest_plan
            if str(item.get("target_path") or "").strip() == "assets/cover.png"
        ),
        "",
    )
    return {
        "schemaVersion": "1.0",
        "title": str(
            state.development_brief.get("title")
            or state.game_spec.get("title")
            or state.game_plan.get("title")
            or "Generated Game"
        ).strip(),
        "description": str(
            state.game_plan.get("introduction")
            or state.development_brief.get("gameplay_goal")
            or ""
        ).strip(),
        "entry": "index.html",
        "styles": ["style.css"],
        "scripts": ["game.js"],
        "assets": referenced_assets,
        "cover": planned_cover,
        "controls": [str(state.development_brief.get("controls") or "").strip()],
        "runtime": "html5-iframe",
        "generatedAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }


def _build_code_file_record(relative_path: str, absolute_path: Any) -> dict[str, str]:
    return {
        "relative_path": relative_path,
        "absolute_path": str(absolute_path),
    }

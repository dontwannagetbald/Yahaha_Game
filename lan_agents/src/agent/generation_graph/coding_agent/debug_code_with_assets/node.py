"""Coding Agent node that debugs drafted code after assets are ready."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent.generation_graph.state import GenerationState
from agent.generation_graph.tools.asset_references import (
    check_asset_references,
    collect_asset_references_from_bundle,
)
from agent.generation_graph.tools.runtime_check import run_headless_runtime_check
from agent.generation_graph.tools.runtime_protocol import ensure_game_ready_signal
from agent.generation_graph.tools.workspace import write_workspace_text
from agent.providers import LLMMessage, LLMProvider, ProviderError


DEBUG_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "index_html": {"type": "string"},
        "style_css": {"type": "string"},
        "game_js": {"type": "string"},
        "manifest_draft": {"type": "object"},
        "repair_notes": {
            "oneOf": [
                {"type": "array"},
                {"type": "string"},
            ]
        },
    },
}

DEBUG_SYSTEM_PROMPT = """
You are the Step-6 Coding Debug Agent for Yahaha_Play.

Return one compact JSON object. You may update:
- index_html
- style_css
- game_js
- manifest_draft
- repair_notes

Rules:
- only repair code or manifest problems inside artifact_workspace
- do not invent new asset paths beyond asset_manifest_plan
- do not remove required runtime assets just to silence errors
- keep output compact and JSON-safe
- prefer single quotes inside HTML, CSS, and JS
- preserve sandbox-safe static HTML5 runtime rules
- game_js must call window.parent.postMessage({ type: 'game_ready' }, '*') after initialization so Play can mark the iframe ready
""".strip()


def debug_code_with_assets(
    state: GenerationState, provider: LLMProvider | None = None
) -> dict[str, Any]:
    """Run one debug pass with real assets available."""
    bundle_context = _build_bundle_context(state)
    initial_asset_check = check_asset_references(bundle_context)
    initial_runtime_check = run_headless_runtime_check(
        str(bundle_context["code_artifacts"]["index_html_path"])
    )

    fixed_issues: list[dict[str, Any]] = []
    unresolved_issues = _collect_unresolved_issues(
        initial_asset_check, initial_runtime_check
    )

    deterministic_ready_repair = _repair_missing_game_ready_signal_if_safe(
        state, bundle_context, initial_runtime_check
    )

    if deterministic_ready_repair:
        bundle_context = _build_bundle_context(state)
        _sync_manifest_draft_with_bundle(state, bundle_context)
        bundle_context = _build_bundle_context(state)
        final_asset_check = check_asset_references(bundle_context)
        final_runtime_check = run_headless_runtime_check(
            str(bundle_context["code_artifacts"]["index_html_path"])
        )
        fixed_issues = _collect_fixed_issues(
            initial_asset_check,
            initial_runtime_check,
            final_asset_check,
            final_runtime_check,
        )
        unresolved_issues = _collect_unresolved_issues(
            final_asset_check, final_runtime_check
        )
        asset_check = final_asset_check
        runtime_check = final_runtime_check
        repair_notes = deterministic_ready_repair
    elif provider and _needs_repair(
        initial_asset_check,
        initial_runtime_check,
        state.validation_report,
    ):
        repair_update = _attempt_repair(state, bundle_context, provider)
        if repair_update:
            bundle_context = _build_bundle_context(state)
            provider_runtime_check = run_headless_runtime_check(
                str(bundle_context["code_artifacts"]["index_html_path"])
            )
            deterministic_ready_repair = _repair_missing_game_ready_signal_if_safe(
                state, bundle_context, provider_runtime_check
            )
            if deterministic_ready_repair:
                repair_update = [*repair_update, *deterministic_ready_repair]
                bundle_context = _build_bundle_context(state)
            _sync_manifest_draft_with_bundle(state, bundle_context)
            bundle_context = _build_bundle_context(state)
            final_asset_check = check_asset_references(bundle_context)
            final_runtime_check = run_headless_runtime_check(
                str(bundle_context["code_artifacts"]["index_html_path"])
            )
            fixed_issues = _collect_fixed_issues(
                initial_asset_check,
                initial_runtime_check,
                final_asset_check,
                final_runtime_check,
            )
            unresolved_issues = _collect_unresolved_issues(
                final_asset_check, final_runtime_check
            )
            asset_check = final_asset_check
            runtime_check = final_runtime_check
            repair_notes = repair_update
        else:
            asset_check = initial_asset_check
            runtime_check = initial_runtime_check
            repair_notes = []
    else:
        asset_check = initial_asset_check
        runtime_check = initial_runtime_check
        repair_notes = []

    state.code_artifacts = bundle_context["code_artifacts"]
    state.integrated_bundle_context = bundle_context

    return {
        "code_artifacts": bundle_context["code_artifacts"],
        "manifest_draft": state.manifest_draft,
        "debug_report": {
            "attempted": True,
            "runtime_check": runtime_check,
            "asset_reference_check": asset_check,
            "fixed_issues": fixed_issues,
            "unresolved_issues": unresolved_issues,
            "notes": repair_notes,
        },
        "generation_status": "validating",
    }


def _build_bundle_context(state: GenerationState) -> dict[str, Any]:
    if not state.code_artifacts or not state.manifest_draft:
        raise ProviderError("debug_code_with_assets requires drafted code and manifest")
    return {
        "code_artifacts": _refresh_code_artifacts(state.code_artifacts),
        "manifest_draft": state.manifest_draft,
        "processed_assets": state.processed_assets,
        "asset_manifest_plan": state.asset_manifest_plan,
        "artifact_workspace": state.artifact_workspace,
    }


def _refresh_code_artifacts(code_artifacts: dict[str, Any]) -> dict[str, Any]:
    refreshed = dict(code_artifacts)
    refreshed["referenced_asset_paths"] = collect_asset_references_from_bundle(code_artifacts)
    return refreshed


def _needs_repair(
    asset_check: dict[str, Any],
    runtime_check: dict[str, Any],
    validation_report: dict[str, Any] | None = None,
) -> bool:
    if validation_report and validation_report.get("valid") is False:
        return True
    if asset_check["issues"]:
        return False
    if asset_check["manifest_missing_from_code"] or asset_check["code_missing_from_manifest"]:
        return True
    return not bool(runtime_check["passed"])


def _attempt_repair(
    state: GenerationState,
    bundle_context: dict[str, Any],
    provider: LLMProvider,
) -> list[str]:
    response = provider.complete_json(
        messages=_build_repair_messages(state, bundle_context),
        response_schema=DEBUG_RESPONSE_SCHEMA,
        temperature=1.0,
        max_completion_tokens=2600,
    )
    repair_notes = _normalize_repair_notes(response.get("repair_notes"))
    workspace = Path(state.artifact_workspace)
    if isinstance(response.get("index_html"), str) and response["index_html"].strip():
        path = workspace / "index.html"
        write_workspace_text(workspace, "index.html", response["index_html"].strip())
        state.code_artifacts["index_html_path"] = str(path)
    if isinstance(response.get("style_css"), str) and response["style_css"].strip():
        path = workspace / "style.css"
        write_workspace_text(workspace, "style.css", response["style_css"].strip())
        state.code_artifacts["style_css_path"] = str(path)
    if isinstance(response.get("game_js"), str) and response["game_js"].strip():
        path = workspace / "game.js"
        write_workspace_text(workspace, "game.js", response["game_js"].strip())
        state.code_artifacts["game_js_path"] = str(path)
    if isinstance(response.get("manifest_draft"), dict) and response["manifest_draft"]:
        state.manifest_draft = response["manifest_draft"]
        manifest_path = workspace / "manifest_draft.json"
        write_workspace_text(
            workspace,
            "manifest_draft.json",
            json.dumps(state.manifest_draft, ensure_ascii=False, indent=2),
        )
        state.code_artifacts["manifest_draft_path"] = str(manifest_path)
    return repair_notes


def _repair_missing_game_ready_signal_if_safe(
    state: GenerationState,
    bundle_context: dict[str, Any],
    runtime_check: dict[str, Any],
) -> list[str]:
    if not runtime_check.get("js_syntax_ok"):
        return []
    if runtime_check.get("game_ready_signal_found"):
        return []
    game_js_path = Path(bundle_context["code_artifacts"]["game_js_path"])
    current_js = game_js_path.read_text(encoding="utf-8")
    next_js = ensure_game_ready_signal(current_js)
    if next_js == current_js:
        return []
    write_workspace_text(Path(state.artifact_workspace), "game.js", next_js)
    state.code_artifacts["game_js_path"] = str(game_js_path)
    return ["restored game_ready signal with deterministic runtime protocol guard"]


def _sync_manifest_draft_with_bundle(
    state: GenerationState, bundle_context: dict[str, Any]
) -> None:
    referenced_assets = list(
        bundle_context["code_artifacts"].get("referenced_asset_paths", [])
    )
    current_assets = [
        str(path).strip()
        for path in (state.manifest_draft or {}).get("assets", [])
        if str(path).strip()
    ]
    if referenced_assets == current_assets:
        return

    state.manifest_draft = dict(state.manifest_draft or {})
    state.manifest_draft["assets"] = referenced_assets
    workspace = Path(state.artifact_workspace)
    manifest_path = workspace / "manifest_draft.json"
    write_workspace_text(
        workspace,
        "manifest_draft.json",
        json.dumps(state.manifest_draft, ensure_ascii=False, indent=2),
    )
    state.code_artifacts["manifest_draft_path"] = str(manifest_path)


def _build_repair_messages(
    state: GenerationState, bundle_context: dict[str, Any]
) -> list[LLMMessage]:
    payload = {
        "development_brief": state.development_brief,
        "asset_manifest_plan": state.asset_manifest_plan,
        "manifest_draft": state.manifest_draft,
        "referenced_asset_paths": bundle_context["code_artifacts"].get(
            "referenced_asset_paths", []
        ),
        "runtime_check": run_headless_runtime_check(
            str(bundle_context["code_artifacts"]["index_html_path"])
        ),
        "asset_reference_check": check_asset_references(bundle_context),
        "validation_report": state.validation_report,
        "current_files": {
            "index_html": Path(
                bundle_context["code_artifacts"]["index_html_path"]
            ).read_text(encoding="utf-8"),
            "style_css": Path(
                bundle_context["code_artifacts"]["style_css_path"]
            ).read_text(encoding="utf-8"),
            "game_js": Path(
                bundle_context["code_artifacts"]["game_js_path"]
            ).read_text(encoding="utf-8"),
        },
    }
    return [
        LLMMessage(role="system", content=DEBUG_SYSTEM_PROMPT),
        LLMMessage(role="user", content=json.dumps(payload, ensure_ascii=False)),
    ]


def _normalize_repair_notes(value: Any) -> list[str]:
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _collect_unresolved_issues(
    asset_check: dict[str, Any], runtime_check: dict[str, Any]
) -> list[dict[str, Any]]:
    issues = list(asset_check["issues"])
    if asset_check["manifest_missing_from_code"]:
        issues.append(
            {
                "kind": "manifest_extra_assets",
                "code": "manifest_extra_assets",
                "assets": asset_check["manifest_missing_from_code"],
                "message": "manifest_draft lists assets not referenced by code",
            }
        )
    if asset_check["code_missing_from_manifest"]:
        issues.append(
            {
                "kind": "manifest_missing_assets",
                "code": "manifest_missing_assets",
                "assets": asset_check["code_missing_from_manifest"],
                "message": "code references assets that are missing from manifest_draft",
            }
        )
    if not runtime_check["js_syntax_ok"]:
        issues.append(
            {
                "kind": "js_syntax_error",
                "code": "js_syntax_error",
                "message": runtime_check["syntax_error"] or "game.js syntax check failed",
            }
        )
    if runtime_check["js_syntax_ok"] and not runtime_check["game_ready_signal_found"]:
        issues.append(
            {
                "kind": "game_ready_signal_missing",
                "code": "game_ready_signal_missing",
                "message": "game.js is missing a game_ready signal",
            }
        )
    if runtime_check["js_syntax_ok"] and not runtime_check["render_signal_found"]:
        issues.append(
            {
                "kind": "render_signal_missing",
                "code": "render_signal_missing",
                "message": "game.js does not appear to render a visible scene",
            }
        )
    if runtime_check["js_syntax_ok"] and not runtime_check.get("interaction_signal_found", True):
        issues.append(
            {
                "kind": "interaction_signal_missing",
                "code": "interaction_signal_missing",
                "message": "game.js does not appear to register player input controls",
            }
        )
    return issues


def _collect_fixed_issues(
    initial_asset_check: dict[str, Any],
    initial_runtime_check: dict[str, Any],
    final_asset_check: dict[str, Any],
    final_runtime_check: dict[str, Any],
) -> list[dict[str, Any]]:
    fixed = []
    if (
        not initial_runtime_check["js_syntax_ok"]
        and final_runtime_check["js_syntax_ok"]
    ):
        fixed.append(
            {
                "kind": "js_syntax_error",
                "message": "Repaired game.js syntax issues",
            }
        )
    if (
        initial_asset_check["code_missing_from_manifest"]
        and not final_asset_check["code_missing_from_manifest"]
    ):
        fixed.append(
            {
                "kind": "manifest_missing_assets",
                "message": "Aligned manifest_draft.assets with code references",
            }
        )
    if (
        initial_asset_check["manifest_missing_from_code"]
        and not final_asset_check["manifest_missing_from_code"]
    ):
        fixed.append(
            {
                "kind": "manifest_extra_assets",
                "message": "Removed stale manifest_draft asset entries",
            }
        )
    if (
        not initial_runtime_check["game_ready_signal_found"]
        and final_runtime_check["game_ready_signal_found"]
    ):
        fixed.append(
            {
                "kind": "game_ready_signal_missing",
                "message": "Restored game_ready signal",
            }
        )
    if (
        not initial_runtime_check.get("interaction_signal_found", True)
        and final_runtime_check.get("interaction_signal_found", False)
    ):
        fixed.append(
            {
                "kind": "interaction_signal_missing",
                "message": "Restored player input controls",
            }
        )
    return fixed

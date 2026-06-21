"""Validator Agent final delivery gate."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from agent.generation_graph.state import GenerationState


REQUIRED_MANIFEST_FIELDS = {
    "entry",
    "styles",
    "scripts",
    "assets",
    "cover",
    "runtime",
    "generatedAt",
}
SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{6,}"),
    re.compile(r"(?i)\b(api[_-]?key|token|password|oauth[_-]?code)\b\s*[:=]"),
    re.compile(r"X-Amz-Signature=", re.IGNORECASE),
    re.compile(r"Signature=", re.IGNORECASE),
]
EXTERNAL_URL_PATTERN = re.compile(r"https?://[^\s'\"<>]+", re.IGNORECASE)


def validate_final_delivery(state: GenerationState) -> dict[str, Any]:
    """Validate the final static bundle without repairing or mutating files."""
    workspace = Path(state.artifact_workspace).expanduser().resolve()
    issues: list[dict[str, Any]] = []

    manifest = _load_manifest(state, workspace, issues)
    _validate_required_files(state, workspace, manifest, issues)
    _validate_manifest_schema(manifest, issues)
    _validate_manifest_assets(state, workspace, manifest, issues)
    _validate_paths_stay_in_workspace(state, workspace, manifest, issues)
    _scan_bundle_for_security_issues(state, workspace, manifest, issues)
    _validate_debug_report(state.debug_report, issues)

    valid = not issues
    validation_report = {
        "valid": valid,
        "issues": issues,
        "checked_files": _checked_files(manifest),
        "manifest": {
            "entry": manifest.get("entry", ""),
            "styles": manifest.get("styles", []),
            "scripts": manifest.get("scripts", []),
            "assets": manifest.get("assets", []),
            "cover": manifest.get("cover", ""),
            "runtime": manifest.get("runtime", ""),
        },
    }
    if valid:
        return {
            "generation_status": "succeeded",
            "validation_report": validation_report,
            "artifact_result": {
                "workspace": str(workspace),
                "manifest_path": str(workspace / "manifest.json"),
                "entry_path": str(workspace / str(manifest.get("entry", "index.html"))),
                "asset_paths": list(manifest.get("assets") or []),
                "cover_path": str(manifest.get("cover") or ""),
            },
            "draft_game_meta": {
                "title": str(manifest.get("title") or state.game_plan.get("title") or ""),
                "description": str(
                    manifest.get("description")
                    or state.game_plan.get("introduction")
                    or ""
                ),
                "tags": list(state.game_plan.get("tags") or []),
                "cover_path": str(manifest.get("cover") or ""),
                "manifest_path": "manifest.json",
                "entry_path": str(manifest.get("entry") or "index.html"),
            },
            "agent_logs": [
                *state.agent_logs,
                {
                    "step": "validator_agent",
                    "level": "info",
                    "message": "Final delivery validation passed.",
                },
            ],
        }

    summary = _summarize_issues(issues)
    return {
        "generation_status": "failed",
        "failed_step": "validator_agent",
        "error_message": summary,
        "retry_hint": "请重新生成游戏，或调整素材后再试。",
        "validation_report": validation_report,
        "agent_logs": [
            *state.agent_logs,
            {
                "step": "validator_agent",
                "level": "error",
                "message": summary,
            },
        ],
    }


def _load_manifest(
    state: GenerationState, workspace: Path, issues: list[dict[str, Any]]
) -> dict[str, Any]:
    manifest_path = _manifest_path(state, workspace)
    if not manifest_path.exists():
        issues.append(
            {
                "kind": "missing_manifest",
                "path": "manifest.json",
                "message": "manifest.json is missing.",
            }
        )
        return dict(state.manifest_draft or {})
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        issues.append(
            {
                "kind": "invalid_manifest_json",
                "path": "manifest.json",
                "message": "manifest.json is not valid JSON.",
            }
        )
        return dict(state.manifest_draft or {})


def _manifest_path(state: GenerationState, workspace: Path) -> Path:
    candidate = str(state.code_artifacts.get("manifest_path") or "").strip()
    if candidate:
        path = Path(candidate).expanduser().resolve()
        if _is_inside(path, workspace):
            return path
    return workspace / "manifest.json"


def _validate_required_files(
    state: GenerationState,
    workspace: Path,
    manifest: dict[str, Any],
    issues: list[dict[str, Any]],
) -> None:
    required_paths = [
        str(manifest.get("entry") or "index.html"),
        *[str(path) for path in manifest.get("styles", [])],
        *[str(path) for path in manifest.get("scripts", [])],
        "manifest.json",
    ]
    for relative_path in required_paths:
        path = _safe_join(workspace, relative_path)
        if path is None or not path.exists():
            issues.append(
                {
                    "kind": "missing_bundle_file",
                    "path": relative_path,
                    "message": f"{relative_path} is missing.",
                }
            )
    for item in state.code_artifacts.get("files", []):
        absolute = str(item.get("absolute_path") or "")
        relative = str(item.get("relative_path") or "")
        if not absolute:
            continue
        path = Path(absolute).expanduser().resolve()
        if not _is_inside(path, workspace):
            issues.append(
                {
                    "kind": "path_outside_workspace",
                    "path": relative or absolute,
                    "message": "Code artifact path escapes artifact_workspace.",
                }
            )


def _validate_manifest_schema(manifest: dict[str, Any], issues: list[dict[str, Any]]) -> None:
    for field in sorted(REQUIRED_MANIFEST_FIELDS - set(manifest.keys())):
        issues.append(
            {
                "kind": "missing_manifest_field",
                "field": field,
                "message": f"manifest field {field} is missing.",
            }
        )
    if manifest.get("runtime") != "html5-iframe":
        issues.append(
            {
                "kind": "invalid_runtime",
                "field": "runtime",
                "message": "manifest.runtime must be html5-iframe.",
            }
        )
    for field in ("styles", "scripts", "assets"):
        if field in manifest and not isinstance(manifest.get(field), list):
            issues.append(
                {
                    "kind": "invalid_manifest_field",
                    "field": field,
                    "message": f"manifest.{field} must be a list.",
                }
            )


def _validate_manifest_assets(
    state: GenerationState,
    workspace: Path,
    manifest: dict[str, Any],
    issues: list[dict[str, Any]],
) -> None:
    planned_runtime_assets = {
        str(item.get("target_path") or "")
        for item in state.asset_manifest_plan
        if item.get("runtime_required")
    }
    manifest_assets = {
        str(path).strip() for path in manifest.get("assets", []) if str(path).strip()
    }
    cover = str(manifest.get("cover") or "").strip()
    if not cover:
        issues.append(
            {
                "kind": "missing_cover",
                "path": "",
                "message": "manifest.cover is missing.",
            }
        )
    elif not _relative_file_exists(workspace, cover):
        issues.append(
            {
                "kind": "missing_cover",
                "path": cover,
                "message": f"{cover} is missing.",
            }
        )

    for path in sorted(planned_runtime_assets | manifest_assets):
        if not path:
            continue
        if not _relative_file_exists(workspace, path):
            issues.append(
                {
                    "kind": "missing_asset",
                    "path": path,
                    "runtime_required": path in planned_runtime_assets,
                    "message": f"{path} is missing.",
                }
            )


def _validate_paths_stay_in_workspace(
    state: GenerationState,
    workspace: Path,
    manifest: dict[str, Any],
    issues: list[dict[str, Any]],
) -> None:
    relative_paths = [
        str(manifest.get("entry") or ""),
        str(manifest.get("cover") or ""),
        *[str(path) for path in manifest.get("styles", [])],
        *[str(path) for path in manifest.get("scripts", [])],
        *[str(path) for path in manifest.get("assets", [])],
        *[
            str(item.get("target_path") or "")
            for item in state.asset_manifest_plan
            if item.get("target_path")
        ],
    ]
    for relative_path in relative_paths:
        if not relative_path:
            continue
        if _safe_join(workspace, relative_path) is None:
            issues.append(
                {
                    "kind": "path_outside_workspace",
                    "path": relative_path,
                    "message": "Bundle path escapes artifact_workspace.",
                }
            )


def _scan_bundle_for_security_issues(
    state: GenerationState,
    workspace: Path,
    manifest: dict[str, Any],
    issues: list[dict[str, Any]],
) -> None:
    paths = [
        str(manifest.get("entry") or "index.html"),
        *[str(path) for path in manifest.get("styles", [])],
        *[str(path) for path in manifest.get("scripts", [])],
        "manifest.json",
    ]
    seen: set[str] = set()
    for relative_path in paths:
        if relative_path in seen:
            continue
        seen.add(relative_path)
        path = _safe_join(workspace, relative_path)
        if path is None or not path.exists() or not path.is_file():
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        if any(pattern.search(content) for pattern in SECRET_PATTERNS):
            issues.append(
                {
                    "kind": "secret_detected",
                    "path": relative_path,
                    "message": "Potential secret or signed URL detected.",
                }
            )
        for url in EXTERNAL_URL_PATTERN.findall(content):
            if url.startswith(("http://localhost", "http://127.0.0.1")):
                continue
            issues.append(
                {
                    "kind": "external_cdn_detected",
                    "path": relative_path,
                    "message": "External URL detected in static bundle.",
                }
            )
            break


def _validate_debug_report(
    debug_report: dict[str, Any], issues: list[dict[str, Any]]
) -> None:
    if not debug_report or not debug_report.get("attempted"):
        issues.append(
            {
                "kind": "missing_debug_report",
                "message": "debug_report is missing or was not attempted.",
            }
        )
        return
    runtime_check = debug_report.get("runtime_check") or {}
    if runtime_check and runtime_check.get("passed") is False:
        runtime_details = _runtime_failure_details(runtime_check)
        issues.append(
            {
                "kind": "runtime_check_failed",
                "message": _format_runtime_failure_message(runtime_details),
                "runtime_details": runtime_details,
            }
        )
    for issue in debug_report.get("unresolved_issues") or []:
        source_message = str(issue.get("message") or "").strip()
        issues.append(
            {
                "kind": "unresolved_debug_issue",
                "source_kind": issue.get("kind", "unknown"),
                "message": (
                    f"debug_report still has unresolved issues: {source_message}"
                    if source_message
                    else "debug_report still has unresolved issues."
                ),
            }
        )


def _runtime_failure_details(runtime_check: dict[str, Any]) -> list[str]:
    details: list[str] = []
    seen: set[str] = set()

    def add_detail(detail: str) -> None:
        normalized = detail.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            details.append(normalized)

    if runtime_check.get("entry_exists") is False:
        add_detail("index.html is missing")
    if runtime_check.get("game_js_exists") is False:
        add_detail("game.js is missing")
    if runtime_check.get("html_has_canvas") is False:
        add_detail("index.html is missing a canvas")
    if runtime_check.get("html_references_game_js") is False:
        add_detail("index.html does not reference game.js")
    if runtime_check.get("node_available") is False:
        add_detail("node is unavailable for JS syntax validation")
    if runtime_check.get("js_syntax_ok") is False:
        syntax_error = str(runtime_check.get("syntax_error") or "").strip()
        add_detail(syntax_error or "game.js syntax check failed")
    if runtime_check.get("game_ready_signal_found") is False:
        add_detail("game_ready signal missing")
    if runtime_check.get("render_signal_found") is False:
        add_detail("render signal missing")
    return details or ["unknown runtime check failure"]


def _format_runtime_failure_message(runtime_details: list[str]) -> str:
    return f"Runtime check did not pass: {'; '.join(runtime_details)}."


def _relative_file_exists(workspace: Path, relative_path: str) -> bool:
    path = _safe_join(workspace, relative_path)
    return bool(path and path.exists() and path.is_file())


def _safe_join(workspace: Path, relative_path: str) -> Path | None:
    normalized = relative_path.strip().replace("\\", "/")
    if not normalized or normalized.startswith("/") or ".." in normalized.split("/"):
        return None
    path = (workspace / normalized).resolve()
    if not _is_inside(path, workspace):
        return None
    return path


def _is_inside(path: Path, workspace: Path) -> bool:
    try:
        path.relative_to(workspace)
    except ValueError:
        return False
    return True


def _checked_files(manifest: dict[str, Any]) -> list[str]:
    return [
        "manifest.json",
        str(manifest.get("entry") or "index.html"),
        *[str(path) for path in manifest.get("styles", [])],
        *[str(path) for path in manifest.get("scripts", [])],
    ]


def _summarize_issues(issues: list[dict[str, Any]]) -> str:
    if not issues:
        return "最终验收失败。"
    first = issues[0]
    path = first.get("path")
    message = str(first.get("message") or "").strip()
    detail = f" - {message}" if message else ""
    if path:
        return f"最终验收失败：{first['kind']} ({path}){detail}。"
    return f"最终验收失败：{first['kind']}{detail}。"

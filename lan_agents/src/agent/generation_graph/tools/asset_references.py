"""Bundle asset reference checks for Coding Agent debug flow."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


ASSET_REFERENCE_PATTERN = re.compile(r"assets/[A-Za-z0-9._/-]+")


def collect_asset_references_from_bundle(code_artifacts: dict[str, Any]) -> list[str]:
    """Collect unique asset references from index/style/js files."""
    contents = _read_bundle_contents(code_artifacts)
    referenced_paths: list[str] = []
    seen = set()
    for content in contents:
        for match in ASSET_REFERENCE_PATTERN.findall(content):
            if match in seen:
                continue
            seen.add(match)
            referenced_paths.append(match)
    return referenced_paths


def check_asset_references(bundle_context: dict[str, Any]) -> dict[str, Any]:
    """Check bundle asset references against processed assets and manifest plan."""
    code_artifacts = bundle_context.get("code_artifacts") or {}
    manifest_draft = bundle_context.get("manifest_draft") or {}
    processed_assets = bundle_context.get("processed_assets") or []
    asset_manifest_plan = bundle_context.get("asset_manifest_plan") or []

    referenced_paths = collect_asset_references_from_bundle(code_artifacts)

    actual_assets = _collect_existing_assets(processed_assets)
    runtime_required_paths = {
        str(item.get("target_path") or "")
        for item in asset_manifest_plan
        if bool(item.get("runtime_required"))
    }
    manifest_assets = [
        str(path).strip()
        for path in manifest_draft.get("assets", [])
        if str(path).strip()
    ]

    issues: list[dict[str, Any]] = []
    missing_references = [path for path in referenced_paths if path not in actual_assets]
    missing_manifest_assets = [path for path in manifest_assets if path not in actual_assets]
    manifest_missing_from_code = [
        path for path in manifest_assets if path not in referenced_paths
    ]
    code_missing_from_manifest = [
        path for path in referenced_paths if path not in manifest_assets
    ]

    for path in missing_references:
        issues.append(
            {
                "kind": "missing_asset",
                "path": path,
                "runtime_required": path in runtime_required_paths,
                "source": "code_reference",
            }
        )
    for path in missing_manifest_assets:
        if path in missing_references:
            continue
        issues.append(
            {
                "kind": "missing_asset",
                "path": path,
                "runtime_required": path in runtime_required_paths,
                "source": "manifest_asset",
            }
        )

    return {
        "passed": not issues
        and not manifest_missing_from_code
        and not code_missing_from_manifest,
        "referenced_asset_paths": referenced_paths,
        "manifest_asset_paths": manifest_assets,
        "available_asset_paths": sorted(actual_assets),
        "missing_asset_paths": [issue["path"] for issue in issues],
        "manifest_missing_from_code": manifest_missing_from_code,
        "code_missing_from_manifest": code_missing_from_manifest,
        "issues": issues,
    }


def _read_bundle_contents(code_artifacts: dict[str, Any]) -> list[str]:
    contents = []
    for key in ("index_html_path", "style_css_path", "game_js_path"):
        path = str(code_artifacts.get(key) or "").strip()
        if not path:
            continue
        file_path = Path(path)
        if not file_path.exists():
            continue
        contents.append(file_path.read_text(encoding="utf-8"))
    return contents


def _collect_existing_assets(processed_assets: list[dict[str, Any]]) -> set[str]:
    actual_assets: set[str] = set()
    for item in processed_assets:
        target_path = str(item.get("target_path") or "").strip()
        file_path = str(item.get("path") or "").strip()
        if not target_path or not file_path:
            continue
        if Path(file_path).exists():
            actual_assets.add(target_path)
    return actual_assets

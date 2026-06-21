"""Run a real-provider smoke test for the stage-B generation graph.

Usage:
    cd lan_agents
    .venv/bin/python scripts/real_generation_smoke.py \
      --fixture src/agent/generation_graph/fixtures/generation_confirmed_session.json \
      --workspace output/real-generation-smoke
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


REQUIRED_ENV = (
    "OPENAI_COMPATIBLE_API_KEY",
    "OPENAI_COMPATIBLE_BASE_URL",
    "OPENAI_COMPATIBLE_MODEL",
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Orchestrator + Coding Agent + Asset Agent with real providers."
    )
    parser.add_argument(
        "--fixture",
        default="src/agent/generation_graph/fixtures/generation_confirmed_session.json",
        help="Confirmed generation fixture JSON.",
    )
    parser.add_argument(
        "--workspace",
        default="output/real-generation-smoke",
        help="Output workspace for generated bundle and assets.",
    )
    parser.add_argument(
        "--no-visual-assets",
        action="store_true",
        help="Clear uploaded image/video assets; cover should still be generated.",
    )
    parser.add_argument(
        "--skip-real-images",
        action="store_true",
        help="Use real LLMs but mock image generation. Useful when image API is down.",
    )
    parser.add_argument(
        "--print-output",
        action="store_true",
        help="Print full generation demo output instead of only the compact summary.",
    )
    args = parser.parse_args()

    _load_dotenv(REPO_ROOT / ".env")
    _load_dotenv(ROOT / ".env")
    _force_real_provider(skip_real_images=args.skip_real_images)
    _print_provider_config(skip_real_images=args.skip_real_images)

    missing = [name for name in REQUIRED_ENV if not os.getenv(name)]
    if missing:
        print(f"[real-smoke] missing required env: {', '.join(missing)}", file=sys.stderr)
        return 2

    from agent.generation_graph.demo import run_generation_demo
    from agent.providers import ProviderError

    fixture_path = _resolve_path(args.fixture)
    workspace = _resolve_path(args.workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

    try:
        result = run_generation_demo(
            fixture=fixture,
            workspace=str(workspace),
            no_visual_assets=args.no_visual_assets,
            use_real_provider=True,
        )
    except ProviderError as exc:
        print(f"[real-smoke] provider failed: {exc}", file=sys.stderr)
        if os.getenv("REAL_SMOKE_DEBUG_TRACEBACK", "").lower() == "true":
            traceback.print_exc()
        return 1
    except Exception as exc:  # noqa: BLE001 - smoke test should expose unexpected failures.
        print(f"[real-smoke] unexpected failure: {type(exc).__name__}: {exc}", file=sys.stderr)
        if os.getenv("REAL_SMOKE_DEBUG_TRACEBACK", "").lower() == "true":
            traceback.print_exc()
        return 1

    summary = _build_summary(result["final_state"], workspace)
    summary_path = workspace / "real_smoke_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if args.print_output:
        print(result["output"])
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"[real-smoke] summary: {summary_path}")
    return 0 if _summary_passed(summary) else 1


def _force_real_provider(*, skip_real_images: bool) -> None:
    os.environ["LLM_PROVIDER"] = "openai-compatible"
    if skip_real_images:
        os.environ["ASSET_IMAGE_PROVIDER"] = "mock"
    else:
        os.environ["ASSET_IMAGE_PROVIDER"] = "openai-compatible"
    os.environ.setdefault("LLM_TIMEOUT_SECONDS", "120")
    os.environ.setdefault("OPENAI_IMAGE_TIMEOUT_SECONDS", "240")


def _print_provider_config(*, skip_real_images: bool) -> None:
    print("[real-smoke] LLM_PROVIDER=openai-compatible")
    print(f"[real-smoke] OPENAI_COMPATIBLE_BASE_URL={os.getenv('OPENAI_COMPATIBLE_BASE_URL', '')}")
    print(f"[real-smoke] OPENAI_COMPATIBLE_MODEL={os.getenv('OPENAI_COMPATIBLE_MODEL', '')}")
    if skip_real_images:
        print("[real-smoke] ASSET_IMAGE_PROVIDER=mock")
    else:
        print("[real-smoke] ASSET_IMAGE_PROVIDER=openai-compatible")
        print(f"[real-smoke] OPENAI_IMAGE_BASE_URL={os.getenv('OPENAI_IMAGE_BASE_URL') or os.getenv('OPENAI_COMPATIBLE_BASE_URL', '')}")
        print(f"[real-smoke] OPENAI_IMAGE_MODEL={os.getenv('OPENAI_IMAGE_MODEL', '')}")


def _build_summary(state: dict[str, Any], workspace: Path) -> dict[str, Any]:
    manifest_paths = [
        str(item.get("target_path") or "")
        for item in state.get("asset_manifest_plan", [])
        if item.get("target_path")
    ]
    processed_paths = [
        str(item.get("target_path") or "")
        for item in state.get("processed_assets", [])
        if item.get("target_path")
    ]
    files = {
        "index": workspace / "index.html",
        "style": workspace / "style.css",
        "script": workspace / "game.js",
        "manifest": workspace / "manifest.json",
        "manifest_draft": workspace / "manifest_draft.json",
        "background": workspace / "assets" / "background.png",
        "player": workspace / "assets" / "player.png",
        "cover": workspace / "assets" / "cover.png",
    }
    debug_report = state.get("debug_report", {})
    manifest_draft = state.get("manifest_draft", {})
    return {
        "generation_status": state.get("generation_status"),
        "status": state.get("status"),
        "workspace": str(workspace),
        "manifest_paths": manifest_paths,
        "processed_paths": processed_paths,
        "referenced_asset_paths": state.get("code_artifacts", {}).get(
            "referenced_asset_paths", []
        ),
        "manifest_assets": manifest_draft.get("assets", []),
        "manifest_cover": manifest_draft.get("cover", ""),
        "files_exist": {key: path.exists() for key, path in files.items()},
        "processed_asset_sources": {
            str(item.get("target_path") or ""): str(item.get("source") or "")
            for item in state.get("processed_assets", [])
            if item.get("target_path")
        },
        "runtime_passed": bool(debug_report.get("runtime_check", {}).get("passed")),
        "asset_check_passed": bool(
            debug_report.get("asset_reference_check", {}).get("passed")
        ),
        "unresolved_issues": debug_report.get("unresolved_issues", []),
        "debug_report": debug_report,
        "validation_valid": bool(
            state.get("validation_report", {}).get("valid")
        ),
        "artifact_manifest_path": state.get("artifact_result", {}).get(
            "manifest_path", ""
        ),
    }


def _summary_passed(summary: dict[str, Any]) -> bool:
    required_files = ["index", "style", "script", "manifest", "manifest_draft", "cover"]
    files_exist = summary.get("files_exist", {})
    return (
        summary.get("generation_status") == "succeeded"
        and summary.get("status") == "succeeded"
        and summary.get("manifest_cover") == "assets/cover.png"
        and all(files_exist.get(name) for name in required_files)
        and summary.get("runtime_passed") is True
        and summary.get("asset_check_passed") is True
        and summary.get("validation_valid") is True
        and summary.get("unresolved_issues") == []
    )


def _resolve_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return ROOT / path


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


if __name__ == "__main__":
    raise SystemExit(main())

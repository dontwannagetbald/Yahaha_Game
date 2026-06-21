import json
from pathlib import Path

from agent.generation_graph.demo import run_generation_demo
from scripts.real_generation_smoke import _build_summary, _summary_passed


def _load_generation_fixture() -> dict:
    fixture_path = (
        Path(__file__).parents[2]
        / "src"
        / "agent"
        / "generation_graph"
        / "fixtures"
        / "generation_confirmed_session.json"
    )
    return json.loads(fixture_path.read_text())


def test_run_generation_demo_prints_summary_and_writes_bundle(tmp_path: Path) -> None:
    result = run_generation_demo(
        fixture=_load_generation_fixture(),
        workspace=str(tmp_path / "generation-demo"),
    )

    output = result["output"]
    workspace = Path(result["workspace"])
    assert "[Orchestrator Asset Decisions]" in output
    assert "[Coding Agent Brief]" in output
    assert "[Asset Agent Brief]" in output
    assert "[Generated Files]" in output
    assert "[Debug Report]" in output
    assert "[Validation Report]" in output
    assert "[Artifact Result]" in output
    assert (workspace / "index.html").exists()
    assert (workspace / "style.css").exists()
    assert (workspace / "game.js").exists()
    assert (workspace / "manifest_draft.json").exists()
    assert (workspace / "manifest.json").exists()
    assert (workspace / "assets" / "background.png").exists()
    assert (workspace / "assets" / "player.png").exists()
    assert (workspace / "assets" / "cover.png").exists()


def test_run_generation_demo_can_skip_visual_assets(tmp_path: Path) -> None:
    fixture = _load_generation_fixture()
    result = run_generation_demo(
        fixture=fixture,
        workspace=str(tmp_path / "generation-demo-no-assets"),
        no_visual_assets=True,
    )

    final_state = result["final_state"]
    workspace = Path(result["workspace"])
    assert [item["target_path"] for item in final_state["asset_manifest_plan"]] == [
        "assets/cover.png"
    ]
    assert [item["target_path"] for item in final_state["processed_assets"]] == [
        "assets/cover.png"
    ]
    assert not (workspace / "assets" / "background.png").exists()
    assert not (workspace / "assets" / "player.png").exists()
    assert (workspace / "assets" / "cover.png").exists()


def test_run_generation_demo_defaults_asset_image_provider_to_mock(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("ASSET_IMAGE_PROVIDER", "openai-compatible")

    result = run_generation_demo(
        fixture=_load_generation_fixture(),
        workspace=str(tmp_path / "generation-demo-mock-image"),
    )

    workspace = Path(result["workspace"])
    assert (workspace / "assets" / "cover.png").exists()
    assert result["final_state"]["generation_status"] == "succeeded"
    assert result["final_state"]["status"] == "succeeded"
    assert result["final_state"]["validation_report"]["valid"] is True
    assert result["final_state"]["debug_report"]["unresolved_issues"] == []


def test_real_generation_smoke_summary_checks_cover_and_debug_status(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "real-smoke-summary"
    (workspace / "assets").mkdir(parents=True)
    for relative_path in (
        "index.html",
        "style.css",
        "game.js",
        "manifest.json",
        "manifest_draft.json",
        "assets/cover.png",
    ):
        (workspace / relative_path).write_text("ok", encoding="utf-8")
    state = {
        "generation_status": "succeeded",
        "status": "succeeded",
        "asset_manifest_plan": [{"target_path": "assets/cover.png"}],
        "processed_assets": [
            {"target_path": "assets/cover.png", "source": "image_model"}
        ],
        "code_artifacts": {"referenced_asset_paths": []},
        "manifest_draft": {"assets": [], "cover": "assets/cover.png"},
        "debug_report": {
            "runtime_check": {"passed": True},
            "asset_reference_check": {"passed": True},
            "unresolved_issues": [],
        },
        "validation_report": {"valid": True},
        "artifact_result": {"manifest_path": str(workspace / "manifest.json")},
    }

    summary = _build_summary(state, workspace)

    assert _summary_passed(summary) is True
    assert summary["manifest_cover"] == "assets/cover.png"
    assert summary["processed_asset_sources"]["assets/cover.png"] == "image_model"

import importlib
import json
from pathlib import Path

import pytest

from agent.generation_graph.graph import generation_graph

pytestmark = pytest.mark.anyio


def _load_generation_fixture(tmp_path: Path) -> dict:
    fixture_path = (
        Path(__file__).parents[2]
        / "src"
        / "agent"
        / "generation_graph"
        / "fixtures"
        / "generation_confirmed_session.json"
    )
    fixture = json.loads(fixture_path.read_text())
    fixture["artifact_workspace"] = str(tmp_path / "artifact_workspace")
    return fixture


async def test_generation_graph_skips_asset_agent_when_assets_are_code_generated(
    tmp_path: Path,
) -> None:
    fixture = _load_generation_fixture(tmp_path)
    fixture["uploaded_assets"] = []
    fixture["material_usage"] = {"assets": []}

    result = await generation_graph.ainvoke(fixture)

    assert result["generation_status"] == "succeeded"
    assert result["status"] == "succeeded"
    manifest_paths = {item["target_path"] for item in result["asset_manifest_plan"]}
    processed_paths = {item["target_path"] for item in result["processed_assets"]}
    assert manifest_paths == {"assets/cover.png"}
    assert processed_paths == {"assets/cover.png"}
    assert result["code_artifacts"]["referenced_asset_paths"] == []
    assert result["manifest_draft"]["cover"] == "assets/cover.png"
    assert result["debug_report"]["attempted"] is True
    assert result["debug_report"]["unresolved_issues"] == []
    assert result["validation_report"]["valid"] is True
    assert result["artifact_result"]["manifest_path"].endswith("manifest.json")
    assert result["draft_game_meta"]["cover_path"] == "assets/cover.png"
    assert [log["step"] for log in result["agent_logs"] if log["level"] == "info"]


async def test_generation_graph_generates_assets_before_debug_when_visual_assets_needed(
    tmp_path: Path,
) -> None:
    fixture = _load_generation_fixture(tmp_path)

    result = await generation_graph.ainvoke(fixture)

    processed_paths = {item["target_path"] for item in result["processed_assets"]}
    manifest_paths = {item["target_path"] for item in result["asset_manifest_plan"]}
    referenced_paths = set(result["code_artifacts"]["referenced_asset_paths"])

    assert result["generation_status"] == "succeeded"
    assert result["status"] == "succeeded"
    assert manifest_paths == {
        "assets/background.png",
        "assets/player.png",
        "assets/cover.png",
    }
    assert processed_paths == {
        "assets/background.png",
        "assets/player.png",
        "assets/cover.png",
    }
    assert referenced_paths == {"assets/background.png", "assets/player.png"}
    assert result["manifest_draft"]["cover"] == "assets/cover.png"
    assert result["debug_report"]["attempted"] is True
    assert result["debug_report"]["unresolved_issues"] == []
    assert result["validation_report"]["valid"] is True
    assert result["artifact_result"]["asset_paths"] == [
        "assets/background.png",
        "assets/player.png",
    ]
    assert result["draft_game_meta"]["title"]


async def test_generation_graph_finalizes_failure_when_validator_rejects_bundle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from agent.generation_graph.validator_agent import validate_final_delivery as real_validate

    def reject_without_repair(state):
        update = real_validate(state)
        update["validation_report"] = {
            "valid": False,
            "issues": [{"kind": "missing_cover", "path": "assets/cover.png"}],
        }
        update["generation_status"] = "failed"
        update["failed_step"] = "validator_agent"
        update["error_message"] = "最终验收失败：missing_cover (assets/cover.png)。"
        update["retry_hint"] = "请重新生成游戏，或调整素材后再试。"
        return update

    graph_module = importlib.import_module("agent.generation_graph.graph")
    monkeypatch.setattr(graph_module, "validate_final_delivery", reject_without_repair)
    fixture = _load_generation_fixture(tmp_path)

    result = await generation_graph.ainvoke(fixture)

    assert result["generation_status"] == "failed"
    assert result["status"] == "failed"
    assert result["failed_step"] == "validator_agent"
    assert result["validation_report"]["valid"] is False
    assert result["error_message"]
    assert result["retry_hint"]
    assert any(log["level"] == "error" for log in result["agent_logs"])

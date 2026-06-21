import json
from copy import deepcopy
from pathlib import Path

from agent.generation_graph.asset_agent.run_asset_agent.node import run_asset_agent
from agent.generation_graph.asset_agent.tools.image_processing import (
    write_chroma_keyed_player,
    write_mock_background,
    write_mock_cover,
)
from agent.generation_graph.orchestrator.planner import deterministic_contracts
from agent.generation_graph.state import GenerationState
from agent.generation_graph.tools.workspace import write_workspace_text


def _build_validated_state(tmp_path: Path) -> GenerationState:
    state = GenerationState(
        job_context={"job_id": "job-validator-test", "user_id": "user-validator-test"},
        user_requirements={
            "intent_summary": "森林里的小猫收集星星小游戏",
            "must_have": ["小猫主角", "收集星星", "森林背景"],
        },
        game_plan={
            "title": "星星小猫冒险",
            "introduction": "帮助小猫在森林里收集星星并避开障碍。",
            "gameplay": "控制小猫左右移动，收集星星得分并躲避障碍。",
            "core_loop": ["观察", "移动", "收集", "躲避"],
            "style": "可爱卡通森林",
            "characters": [{"role": "player", "description": "圆滚滚的小猫"}],
            "win_condition": "倒计时结束分数达标",
            "lose_condition": "生命值归零",
            "controls": "方向键或 WASD 移动",
            "tags": ["arcade", "casual"],
        },
        material_usage={"assets": []},
        uploaded_assets=[],
        artifact_workspace=str(tmp_path / "artifact_workspace"),
    )
    contracts = deterministic_contracts(state)
    state.development_brief = contracts["development_brief"]
    state.asset_work_order = contracts["asset_work_order"]
    state.asset_manifest_plan = [
        {
            "asset_id": "background",
            "target_path": "assets/background.png",
            "kind": "image",
            "required": True,
            "source": "generated",
            "runtime_required": True,
            "display_only": False,
            "logical_width": 1280,
            "logical_height": 720,
            "alpha_required": False,
            "background": "gameplay",
            "fit": "cover",
            "derived_from": "",
            "title_source": "",
        },
        {
            "asset_id": "player",
            "target_path": "assets/player.png",
            "kind": "image",
            "required": True,
            "source": "generated",
            "runtime_required": True,
            "display_only": False,
            "logical_width": 256,
            "logical_height": 256,
            "alpha_required": True,
            "background": "transparent",
            "fit": "contain",
            "derived_from": "",
            "title_source": "",
        },
        {
            "asset_id": "cover",
            "target_path": "assets/cover.png",
            "kind": "image",
            "required": True,
            "source": "generated",
            "runtime_required": False,
            "display_only": True,
            "logical_width": 1280,
            "logical_height": 720,
            "alpha_required": False,
            "background": "cover",
            "fit": "cover",
            "derived_from": "",
            "title_source": "",
        },
    ]
    state.game_spec = contracts["game_spec"]
    _write_mock_assets(state)
    _write_valid_bundle(state)
    return state


def _write_mock_assets(state: GenerationState) -> None:
    workspace = Path(state.artifact_workspace)
    background_path = workspace / "assets" / "background.png"
    player_path = workspace / "assets" / "player.png"
    cover_path = workspace / "assets" / "cover.png"
    write_mock_background(background_path)
    write_chroma_keyed_player(player_path)
    write_mock_cover(cover_path)
    state.processed_assets = [
        {
            "target_path": "assets/background.png",
            "path": str(background_path),
            "runtime_required": True,
        },
        {
            "target_path": "assets/player.png",
            "path": str(player_path),
            "runtime_required": True,
        },
        {
            "target_path": "assets/cover.png",
            "path": str(cover_path),
            "runtime_required": False,
        },
    ]
    state.asset_analysis = []


def _write_valid_bundle(state: GenerationState) -> None:
    workspace = Path(state.artifact_workspace)
    manifest = {
        "schemaVersion": "1.0",
        "title": state.game_plan["title"],
        "description": state.game_plan["introduction"],
        "entry": "index.html",
        "styles": ["style.css"],
        "scripts": ["game.js"],
        "assets": ["assets/background.png", "assets/player.png"],
        "cover": "assets/cover.png",
        "controls": [state.game_plan["controls"]],
        "runtime": "html5-iframe",
        "generatedAt": "2026-06-21T00:00:00Z",
    }
    index_path = write_workspace_text(
        workspace,
        "index.html",
        "<!doctype html><html><head><link rel='stylesheet' href='style.css'></head><body><canvas id='game'></canvas><script src='game.js'></script></body></html>",
    )
    style_path = write_workspace_text(workspace, "style.css", "body { margin: 0; }")
    js_path = write_workspace_text(
        workspace,
        "game.js",
        "const canvas = document.getElementById('game'); const ctx = canvas.getContext('2d'); const bg = 'assets/background.png'; const player = 'assets/player.png'; ctx.fillRect(0, 0, 10, 10); window.parent.postMessage({ type: 'game_ready' }, '*');",
    )
    manifest_path = write_workspace_text(
        workspace,
        "manifest.json",
        json.dumps(manifest, ensure_ascii=False, indent=2),
    )
    state.manifest_draft = manifest
    state.code_artifacts = {
        "index_html_path": str(index_path),
        "style_css_path": str(style_path),
        "game_js_path": str(js_path),
        "manifest_path": str(manifest_path),
        "files": [
            {"relative_path": "index.html", "absolute_path": str(index_path)},
            {"relative_path": "style.css", "absolute_path": str(style_path)},
            {"relative_path": "game.js", "absolute_path": str(js_path)},
            {"relative_path": "manifest.json", "absolute_path": str(manifest_path)},
        ],
        "referenced_asset_paths": ["assets/background.png", "assets/player.png"],
    }
    state.debug_report = {
        "attempted": True,
        "runtime_check": {
            "passed": True,
            "js_syntax_ok": True,
            "game_ready_signal_found": True,
        },
        "unresolved_issues": [],
    }
    state.integrated_bundle_context = {
        "code_artifacts": deepcopy(state.code_artifacts),
        "manifest_draft": deepcopy(state.manifest_draft),
        "processed_assets": deepcopy(state.processed_assets),
        "asset_manifest_plan": deepcopy(state.asset_manifest_plan),
        "artifact_workspace": state.artifact_workspace,
    }


def test_validate_final_delivery_accepts_complete_safe_bundle(tmp_path: Path) -> None:
    from agent.generation_graph.validator_agent.validate_final_delivery.node import (
        validate_final_delivery,
    )

    state = _build_validated_state(tmp_path)

    update = validate_final_delivery(state)

    assert update["generation_status"] == "succeeded"
    assert update["validation_report"]["valid"] is True
    assert update["validation_report"]["issues"] == []
    assert update["artifact_result"]["manifest_path"].endswith("manifest.json")
    assert update["draft_game_meta"]["cover_path"] == "assets/cover.png"
    assert "repair_decision" not in update["validation_report"]
    assert "repair_instruction" not in update["validation_report"]


def test_validate_final_delivery_fails_when_cover_file_is_missing(tmp_path: Path) -> None:
    from agent.generation_graph.validator_agent.validate_final_delivery.node import (
        validate_final_delivery,
    )

    state = _build_validated_state(tmp_path)
    cover = Path(state.artifact_workspace) / "assets" / "cover.png"
    cover.unlink()

    update = validate_final_delivery(state)

    assert update["generation_status"] == "failed"
    assert update["failed_step"] == "validator_agent"
    assert update["validation_report"]["valid"] is False
    assert any(
        issue["kind"] == "missing_cover" and issue["path"] == "assets/cover.png"
        for issue in update["validation_report"]["issues"]
    )


def test_validate_final_delivery_fails_for_missing_entry_and_runtime_asset(
    tmp_path: Path,
) -> None:
    from agent.generation_graph.validator_agent.validate_final_delivery.node import (
        validate_final_delivery,
    )

    state = _build_validated_state(tmp_path)
    Path(state.code_artifacts["index_html_path"]).unlink()
    player = Path(state.artifact_workspace) / "assets" / "player.png"
    player.unlink()

    update = validate_final_delivery(state)

    issue_kinds = {issue["kind"] for issue in update["validation_report"]["issues"]}
    assert update["generation_status"] == "failed"
    assert "missing_bundle_file" in issue_kinds
    assert "missing_asset" in issue_kinds


def test_validate_final_delivery_fails_when_bundle_contains_secret_or_cdn(
    tmp_path: Path,
) -> None:
    from agent.generation_graph.validator_agent.validate_final_delivery.node import (
        validate_final_delivery,
    )

    state = _build_validated_state(tmp_path)
    js_path = Path(state.code_artifacts["game_js_path"])
    js_path.write_text(
        "const apiKey = 'sk-test-secret'; const cdn = 'https://cdn.example.com/game.js';",
        encoding="utf-8",
    )

    update = validate_final_delivery(state)

    issue_kinds = {issue["kind"] for issue in update["validation_report"]["issues"]}
    assert update["generation_status"] == "failed"
    assert "secret_detected" in issue_kinds
    assert "external_cdn_detected" in issue_kinds
    assert "sk-test-secret" not in json.dumps(update, ensure_ascii=False)


def test_validate_final_delivery_fails_when_debug_report_is_missing_or_unresolved(
    tmp_path: Path,
) -> None:
    from agent.generation_graph.validator_agent.validate_final_delivery.node import (
        validate_final_delivery,
    )

    missing_debug_state = _build_validated_state(tmp_path / "missing-debug")
    missing_debug_state.debug_report = {}

    missing_debug_update = validate_final_delivery(missing_debug_state)

    assert missing_debug_update["generation_status"] == "failed"
    assert any(
        issue["kind"] == "missing_debug_report"
        for issue in missing_debug_update["validation_report"]["issues"]
    )

    unresolved_state = _build_validated_state(tmp_path / "unresolved-debug")
    unresolved_state.debug_report["unresolved_issues"] = [
        {"kind": "js_syntax_error", "message": "game.js failed syntax check"}
    ]

    unresolved_update = validate_final_delivery(unresolved_state)

    assert unresolved_update["generation_status"] == "failed"
    assert any(
        issue["kind"] == "unresolved_debug_issue"
        for issue in unresolved_update["validation_report"]["issues"]
    )


def test_validate_final_delivery_prints_runtime_check_failure_details(
    tmp_path: Path,
) -> None:
    from agent.generation_graph.validator_agent.validate_final_delivery.node import (
        validate_final_delivery,
    )

    state = _build_validated_state(tmp_path)
    state.debug_report["runtime_check"] = {
        "passed": False,
        "entry_exists": True,
        "game_js_exists": True,
        "html_has_canvas": True,
        "html_references_game_js": True,
        "node_available": True,
        "js_syntax_ok": True,
        "syntax_error": "",
        "game_ready_signal_found": False,
        "render_signal_found": False,
    }
    state.debug_report["unresolved_issues"] = [
        {
            "kind": "game_ready_signal_missing",
            "message": "game.js is missing a game_ready signal",
        }
    ]

    update = validate_final_delivery(state)

    runtime_issue = next(
        issue
        for issue in update["validation_report"]["issues"]
        if issue["kind"] == "runtime_check_failed"
    )
    assert update["generation_status"] == "failed"
    assert "game_ready signal missing" in runtime_issue["message"]
    assert "render signal missing" in runtime_issue["message"]
    assert runtime_issue["runtime_details"] == [
        "game_ready signal missing",
        "render signal missing",
    ]
    assert "game_ready signal missing" in update["error_message"]


def test_validate_final_delivery_deduplicates_runtime_check_failure_details(
    tmp_path: Path,
) -> None:
    from agent.generation_graph.validator_agent.validate_final_delivery.node import (
        validate_final_delivery,
    )

    state = _build_validated_state(tmp_path)
    state.debug_report["runtime_check"] = {
        "passed": False,
        "entry_exists": True,
        "game_js_exists": True,
        "html_has_canvas": True,
        "html_references_game_js": True,
        "node_available": False,
        "js_syntax_ok": False,
        "syntax_error": "node is unavailable for JS syntax validation",
        "game_ready_signal_found": True,
        "render_signal_found": True,
    }

    update = validate_final_delivery(state)

    runtime_issue = next(
        issue
        for issue in update["validation_report"]["issues"]
        if issue["kind"] == "runtime_check_failed"
    )
    assert runtime_issue["runtime_details"] == [
        "node is unavailable for JS syntax validation"
    ]
    assert (
        runtime_issue["message"].count("node is unavailable for JS syntax validation")
        == 1
    )

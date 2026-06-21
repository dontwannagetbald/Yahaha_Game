import json
from copy import deepcopy
from pathlib import Path

from agent.generation_graph.asset_agent.run_asset_agent.node import run_asset_agent
from agent.generation_graph.orchestrator.planner import deterministic_contracts
from agent.generation_graph.state import GenerationState
from agent.generation_graph.tools.workspace import write_workspace_text
from agent.providers import MockLLMProvider


def _build_state(tmp_path: Path) -> GenerationState:
    state = GenerationState(
        job_context={"job_id": "job-debug-test", "user_id": "user-debug-test"},
        user_requirements={
            "intent_summary": "可爱卡通森林里的小猫收集星星小游戏",
            "must_have": ["小猫主角", "森林背景"],
        },
        game_plan={
            "title": "星星小猫冒险",
            "introduction": "帮助小猫在森林里收集星星并避开障碍。",
            "gameplay": "玩家控制小猫左右移动，收集星星得分并躲避障碍。",
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
    state.asset_manifest_plan = contracts["asset_manifest_plan"]
    state.game_spec = contracts["game_spec"]
    asset_update = run_asset_agent(state)
    state.processed_assets = asset_update["processed_assets"]
    state.asset_analysis = asset_update["asset_analysis"]
    return state


def _write_bundle_files(
    state: GenerationState,
    *,
    index_html: str,
    style_css: str,
    game_js: str,
    manifest_draft: dict,
) -> None:
    workspace = Path(state.artifact_workspace)
    index_path = write_workspace_text(workspace, "index.html", index_html)
    style_path = write_workspace_text(workspace, "style.css", style_css)
    js_path = write_workspace_text(workspace, "game.js", game_js)
    manifest_path = write_workspace_text(
        workspace,
        "manifest_draft.json",
        json.dumps(manifest_draft, ensure_ascii=False, indent=2),
    )
    state.code_artifacts = {
        "index_html_path": str(index_path),
        "style_css_path": str(style_path),
        "game_js_path": str(js_path),
        "manifest_draft_path": str(manifest_path),
        "files": [
            {"relative_path": "index.html", "absolute_path": str(index_path)},
            {"relative_path": "style.css", "absolute_path": str(style_path)},
            {"relative_path": "game.js", "absolute_path": str(js_path)},
            {"relative_path": "manifest_draft.json", "absolute_path": str(manifest_path)},
        ],
        "referenced_asset_paths": ["assets/background.png", "assets/player.png"],
    }
    state.manifest_draft = manifest_draft
    state.integrated_bundle_context = {
        "code_artifacts": deepcopy(state.code_artifacts),
        "manifest_draft": deepcopy(state.manifest_draft),
        "processed_assets": deepcopy(state.processed_assets),
        "asset_manifest_plan": deepcopy(state.asset_manifest_plan),
        "artifact_workspace": state.artifact_workspace,
    }


def test_debug_code_with_assets_reports_missing_runtime_asset_without_mutating_work_order(
    tmp_path: Path,
) -> None:
    from agent.generation_graph.coding_agent.debug_code_with_assets.node import (
        debug_code_with_assets,
    )

    state = _build_state(tmp_path)
    original_work_order = deepcopy(state.asset_work_order)
    state.processed_assets = [
        asset for asset in state.processed_assets if asset["target_path"] != "assets/player.png"
    ]
    manifest_draft = {
        "schemaVersion": "1.0",
        "title": state.game_plan["title"],
        "description": state.game_plan["introduction"],
        "entry": "index.html",
        "styles": ["style.css"],
        "scripts": ["game.js"],
        "assets": [],
        "cover": "",
        "controls": [state.game_plan["controls"]],
        "runtime": "html5-iframe",
    }
    _write_bundle_files(
        state,
        index_html="<!doctype html><html><body><canvas id='game'></canvas><script src='game.js'></script></body></html>",
        style_css="body { margin: 0; }",
        game_js="const bg = 'assets/background.png'; const player = 'assets/player.png'; window.parent.postMessage({ type: 'game_ready' }, '*');",
        manifest_draft=manifest_draft,
    )

    update = debug_code_with_assets(state)

    assert update["debug_report"]["attempted"] is True
    assert update["debug_report"]["unresolved_issues"]
    assert any(
        issue["kind"] == "missing_asset" for issue in update["debug_report"]["unresolved_issues"]
    )
    assert state.asset_work_order == original_work_order


def test_debug_code_with_assets_repairs_js_error_once_and_rechecks(
    tmp_path: Path,
) -> None:
    from agent.generation_graph.coding_agent.debug_code_with_assets.node import (
        debug_code_with_assets,
    )

    state = _build_state(tmp_path)
    manifest_draft = {
        "schemaVersion": "1.0",
        "title": state.game_plan["title"],
        "description": state.game_plan["introduction"],
        "entry": "index.html",
        "styles": ["style.css"],
        "scripts": ["game.js"],
        "assets": [],
        "cover": "",
        "controls": [state.game_plan["controls"]],
        "runtime": "html5-iframe",
    }
    _write_bundle_files(
        state,
        index_html="<!doctype html><html><body><canvas id='game'></canvas><script src='game.js'></script></body></html>",
        style_css="body { margin: 0; }",
        game_js="const broken = ;",
        manifest_draft=manifest_draft,
    )
    provider = MockLLMProvider(
        response={
            "game_js": "const canvas = document.getElementById('game'); const ctx = canvas.getContext('2d'); ctx.fillStyle = '#101418'; ctx.fillRect(0, 0, canvas.width, canvas.height); window.parent.postMessage({ type: 'game_ready' }, '*');",
            "manifest_draft": manifest_draft,
            "repair_notes": ["fixed syntax and restored ready signal"],
        }
    )

    update = debug_code_with_assets(state, provider=provider)

    assert update["generation_status"] == "validating"
    assert update["debug_report"]["attempted"] is True
    assert update["debug_report"]["fixed_issues"]
    assert update["debug_report"]["unresolved_issues"] == []
    assert update["debug_report"]["runtime_check"]["js_syntax_ok"] is True
    assert update["debug_report"]["runtime_check"]["game_ready_signal_found"] is True
    assert len(provider.calls) == 1


def test_debug_code_with_assets_stops_after_one_failed_repair_round(
    tmp_path: Path,
) -> None:
    from agent.generation_graph.coding_agent.debug_code_with_assets.node import (
        debug_code_with_assets,
    )

    state = _build_state(tmp_path)
    manifest_draft = {
        "schemaVersion": "1.0",
        "title": state.game_plan["title"],
        "description": state.game_plan["introduction"],
        "entry": "index.html",
        "styles": ["style.css"],
        "scripts": ["game.js"],
        "assets": [],
        "cover": "",
        "controls": [state.game_plan["controls"]],
        "runtime": "html5-iframe",
    }
    _write_bundle_files(
        state,
        index_html="<!doctype html><html><body><canvas id='game'></canvas><script src='game.js'></script></body></html>",
        style_css="body { margin: 0; }",
        game_js="const broken = ;",
        manifest_draft=manifest_draft,
    )
    provider = MockLLMProvider(
        response={
            "game_js": "const stillBroken = ;",
            "manifest_draft": manifest_draft,
            "repair_notes": ["attempted repair but syntax is still broken"],
        }
    )

    update = debug_code_with_assets(state, provider=provider)

    assert update["debug_report"]["attempted"] is True
    assert update["debug_report"]["unresolved_issues"]
    assert any(
        issue["kind"] == "js_syntax_error"
        for issue in update["debug_report"]["unresolved_issues"]
    )
    assert len(provider.calls) == 1

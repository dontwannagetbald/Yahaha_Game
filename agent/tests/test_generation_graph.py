from __future__ import annotations

import json
from pathlib import Path

from app.graph.generation_graph import run_generation
from app.agents.validator_agent import validate_bundle


def sample_request() -> dict:
    return {
        "job_id": "job-1",
        "user_id": "user-1",
        "prompt": "做一个俯视角霓虹风躲避收集小游戏。",
        "confirmation_card": {
            "title": "霓虹生存者",
            "short_description": "躲避障碍并收集能量",
            "game_type": "arcade survival",
            "core_gameplay": "移动、躲避、收集、存活",
            "win_lose_condition": "倒计时结束前保持生命值大于 0",
            "controls": "方向键或 WASD 移动",
            "assets_used": "上传的机器人图片作为主角参考",
            "tags": ["survival", "neon"],
            "cover_suggestion": "霓虹竞技场中的机器人",
        },
        "structured_design_state": {
            "visual_style": "neon sci-fi",
            "core_loop": ["move", "avoid", "collect", "survive"],
            "win_condition": "survive until timer ends",
            "lose_condition": "hp reaches zero",
            "controls_detail": ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"],
            "player_role": "robot scout",
            "asset_intent": [
                {
                    "asset_id": "asset-1",
                    "suggested_use": "player sprite reference",
                }
            ],
        },
        "uploaded_assets": [
            {
                "asset_id": "asset-1",
                "filename": "robot.png",
                "mime_type": "image/png",
                "size_bytes": 1024,
                "object_key": "uploads/u1/a1/robot.png",
            }
        ],
    }


def test_generation_graph_writes_manifest_and_bundle(tmp_path: Path):
    output_dir = tmp_path / "demo-output"
    result = run_generation(sample_request(), output_dir=output_dir)

    manifest_path = Path(result["artifact"]["manifest_path"])
    entry_path = Path(result["artifact"]["entry_path"])

    assert manifest_path.exists()
    assert entry_path.exists()
    assert (output_dir / "style.css").exists()
    assert (output_dir / "game.js").exists()

    manifest = json.loads(manifest_path.read_text())
    assert manifest["title"] == "霓虹生存者"
    assert manifest["entry"] == "index.html"
    assert result["validation"]["valid"] is True


def test_validator_reports_missing_script(tmp_path: Path):
    output_dir = tmp_path / "invalid-bundle"
    result = run_generation(sample_request(), output_dir=output_dir)
    (output_dir / "game.js").unlink()

    report = validate_bundle(
        bundle_dir=output_dir,
        manifest_path=Path(result["artifact"]["manifest_path"]),
    )

    assert report["valid"] is False
    assert report["failed_step"] == "validate_bundle"
    assert report["error_message"]


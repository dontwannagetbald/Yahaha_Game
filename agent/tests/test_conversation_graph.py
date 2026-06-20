from __future__ import annotations

from app.graph.conversation_graph import run_conversation


def test_conversation_graph_returns_confirmation_and_design_state():
    result = run_conversation(
        {
            "prompt": "做一个俯视角霓虹风躲避收集小游戏，主角是机器人，用户通过方向键移动，活到倒计时结束就算赢。",
            "chat_history": [
                {
                    "role": "user",
                    "content": "我想做一个霓虹科幻风的小游戏，玩家控制机器人在地图里躲障碍和收集能量。",
                }
            ],
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
    )

    confirmation = result["confirmation_card"]
    design_state = result["structured_design_state"]

    assert confirmation["title"]
    assert "躲避" in confirmation["core_gameplay"]
    assert confirmation["controls"]
    assert design_state["core_loop"]
    assert "robot" in str(design_state["asset_intent"]).lower()


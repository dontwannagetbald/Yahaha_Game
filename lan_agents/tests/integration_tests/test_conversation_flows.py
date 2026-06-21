import pytest

from agent import conversation_graph

pytestmark = pytest.mark.anyio


def complete_game_plan() -> dict[str, object]:
    return {
        "plan_id": "plan-existing",
        "title": "星星小猫",
        "introduction": "帮助小猫收集星星",
        "tags": ["arcade", "casual"],
        "gameplay": "躲避障碍并收集星星",
        "core_loop": ["移动", "躲避", "收集"],
        "style": "可爱卡通",
        "characters": ["小猫"],
        "win_condition": "收集10颗星星",
        "lose_condition": "撞到滚石",
        "controls": "方向键移动",
        "suggestions": [],
        "confidence": "medium",
    }


async def test_regenerate_keeps_requirements_constraints_and_assets() -> None:
    inputs = {
        "user_requirements": {
            "intent_summary": "做一个小猫躲避障碍游戏",
            "must_have": ["躲避障碍", "小猫主角"],
            "nice_to_have": ["可爱风格"],
            "constraints": ["不要恐怖"],
            "open_questions": [],
            "answered_questions": [],
            "preference_profile": {
                "genre_candidates": ["arcade", "casual"],
                "visual_style": "可爱",
                "tone": "轻松",
                "target_session_length": None,
                "difficulty": "easy",
            },
            "revision_count": 2,
        },
        "game_plan": complete_game_plan(),
        "material_usage": {
            "assets": [
                {
                    "asset_id": "asset-1",
                    "filename": "cat.png",
                    "mime_type": "image/png",
                    "intended_use": "character",
                    "usage_priority": "primary",
                    "user_hint": "主角",
                    "agent_note": "已记录素材，后续会在生成阶段按用途使用。",
                }
            ]
        },
        "user_event": {"type": "regenerate"},
    }

    res = await conversation_graph.ainvoke(inputs)

    assert res["game_plan"]["plan_id"] != "plan-existing"
    assert res["game_plan"]["title"] != "星星小猫"
    assert res["game_plan"]["introduction"] != "帮助小猫收集星星"
    assert "这版我" in res["game_plan"]["introduction"]
    assert "《" in res["game_plan"]["introduction"]
    assert "目标是收集10颗星星，同时避免撞到滚石" in res["game_plan"]["introduction"]
    assert "操作方式为方向键移动" in res["game_plan"]["introduction"]
    assert res["user_requirements"]["must_have"] == ["躲避障碍", "小猫主角"]
    assert res["user_requirements"]["constraints"] == ["不要恐怖"]
    assert res["material_usage"]["assets"][0]["asset_id"] == "asset-1"


@pytest.mark.parametrize(
    ("game_plan", "material_usage", "expected_handoff", "expected_status"),
    [
        (complete_game_plan(), {"assets": []}, True, "confirmed"),
        (
            {**complete_game_plan(), "win_condition": ""},
            {"assets": []},
            False,
            "collecting",
        ),
        (
            complete_game_plan(),
            {
                "assets": [
                    {
                        "asset_id": "asset-1",
                        "filename": "cat.png",
                        "mime_type": "image/png",
                        "intended_use": "",
                        "usage_priority": "primary",
                        "user_hint": "",
                        "agent_note": "",
                    }
                ]
            },
            False,
            "collecting",
        ),
    ],
)
async def test_confirm_validates_plan_and_material_usage(
    game_plan: dict[str, object],
    material_usage: dict[str, object],
    expected_handoff: bool,
    expected_status: str,
) -> None:
    res = await conversation_graph.ainvoke(
        {
            "game_plan": game_plan,
            "material_usage": material_usage,
            "user_event": {"type": "confirm"},
        }
    )

    assert res["handoff_to_generation"] is expected_handoff
    assert res["conversation_status"] == expected_status

import pytest

from agent import conversation_graph

pytestmark = pytest.mark.anyio


async def test_conversation_graph_loads() -> None:
    inputs = {"user_event": {"type": "chat", "message": "做一个躲避障碍的小游戏"}}
    res = await conversation_graph.ainvoke(inputs)
    assert res is not None
    assert res["conversation_status"] == "collecting"
    assert "躲避障碍" in res["user_requirements"]["intent_summary"]
    assert res["user_requirements"]["must_have"] == []
    assert res["game_plan"]["tags"] == []
    assert res["material_usage"] == {"assets": []}
    assert isinstance(res["assistant_response"]["suggestions"], list)
    assert res["assistant_response"]["card"] is None


@pytest.mark.parametrize(
    ("event", "expected_status", "expected_handoff"),
    [
        ({"type": "chat", "message": "做一个可爱风格的躲避障碍小游戏"}, "ready_to_confirm", False),
        (
            {
                "type": "upload_assets",
                "uploaded_assets": [
                    {
                        "asset_id": "asset-1",
                        "filename": "cat.png",
                        "mime_type": "image/png",
                        "user_hint": "主角",
                    }
                ],
            },
            "ready_to_confirm",
            False,
        ),
        ({"type": "regenerate"}, "ready_to_confirm", False),
        ({"type": "confirm"}, "confirmed", True),
        ({"type": "invalid_kind"}, "error", False),
    ],
)
async def test_conversation_graph_routes_supported_events(
    event: dict[str, object], expected_status: str, expected_handoff: bool
) -> None:
    inputs = {
        "game_plan": {
            "plan_id": "plan-existing",
            "title": "星星小猫",
            "introduction": "帮助小猫收集星星并躲开障碍。",
            "tags": ["arcade", "casual"],
            "gameplay": "左右移动躲避障碍并收集星星。",
            "core_loop": ["移动", "躲避", "收集"],
            "style": "可爱卡通",
            "characters": ["小猫"],
            "win_condition": "收集足够星星",
            "lose_condition": "撞到障碍",
            "controls": "方向键移动",
            "suggestions": [],
            "confidence": "medium",
        },
        "user_event": event,
    }

    res = await conversation_graph.ainvoke(inputs)

    assert res["conversation_status"] == expected_status
    assert res["handoff_to_generation"] is expected_handoff
    assert "assistant_response" in res


async def test_chat_returns_card_only_when_game_plan_is_complete() -> None:
    inputs = {
        "game_plan": {
            "tags": ["arcade", "casual"],
        },
        "user_event": {
            "type": "chat",
            "message": "标题叫星星小猫，介绍是帮助小猫收集星星，玩法是躲避障碍并收集星星，风格是可爱卡通，角色是小猫，胜利条件是收集10颗星星，失败条件是撞到滚石，操作方式是方向键移动。",
        }
    }

    res = await conversation_graph.ainvoke(inputs)

    assert res["conversation_status"] == "ready_to_confirm"
    card = res["assistant_response"]["card"]
    assert card["plan_id"] == res["game_plan"]["plan_id"]
    assert card["title"] == "星星小猫"
    assert card["tags"] == ["arcade", "casual"]
    assert "可爱卡通" in card["introduction"]
    assert "躲避障碍并收集星星" in card["introduction"]
    assert "收集10颗星星" in card["introduction"]
    assert "方向键移动" in card["introduction"]
    assert res["assistant_response"]["actions"] == ["generate", "regenerate"]

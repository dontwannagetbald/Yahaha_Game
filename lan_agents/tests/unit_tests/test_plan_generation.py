from agent.conversation_graph.nodes import build_user_response, generate_or_refine_plan
from agent.state import ConversationState


def test_generate_or_refine_plan_filters_tags_to_mvp_set() -> None:
    state = ConversationState(
        user_requirements={
            **ConversationState().user_requirements,
            "intent_summary": "做一个策略解谜游戏",
            "preference_profile": {
                **ConversationState().user_requirements["preference_profile"],
                "genre_candidates": ["strategy", "unknown", "puzzle"],
                "visual_style": "像素",
            },
        },
        user_event={
            "type": "chat",
            "message": "标题叫机关森林，介绍是解开机关，玩法是推箱子解谜，风格是像素，角色是探险家，胜利条件是打开大门，失败条件是步数用完，操作方式是方向键移动。",
        },
    )

    update = generate_or_refine_plan(state)

    assert update["game_plan"]["tags"] == ["strategy", "puzzle"]
    assert update["game_plan"]["title"] == "机关森林"
    assert update["game_plan"]["win_condition"] == "打开大门"


def test_complete_generated_plan_response_card_uses_only_card_fields() -> None:
    state = ConversationState(
        game_plan={
            "plan_id": "plan-1",
            "title": "机关森林",
            "introduction": "解开机关",
            "tags": ["strategy", "puzzle"],
            "gameplay": "推箱子解谜",
            "core_loop": ["行动", "反馈", "推进"],
            "style": "像素",
            "characters": ["探险家"],
            "win_condition": "打开大门",
            "lose_condition": "步数用完",
            "controls": "方向键移动",
            "suggestions": ["更难一点"],
            "confidence": "medium",
        }
    )

    response = build_user_response(state)["assistant_response"]

    assert set(response["card"]) == {"plan_id", "title", "introduction", "tags"}
    assert response["suggestions"] == []


def test_complete_plan_without_introduction_generates_summary_card() -> None:
    state = ConversationState(
        user_requirements={
            **ConversationState().user_requirements,
            "intent_summary": "用户想做一个小猫在月光森林收集星星并躲开滚石的轻松小游戏。",
            "must_have": ["小猫主角", "收集星星", "躲避滚石"],
            "constraints": ["难度简单"],
        },
        game_plan={
            "plan_id": "plan-cat",
            "title": "星星小猫",
            "introduction": "",
            "tags": ["arcade", "casual"],
            "gameplay": "小猫在月光森林里收集星星并躲避滚石。",
            "core_loop": ["移动", "躲避", "收集"],
            "style": "可爱卡通",
            "characters": ["小猫"],
            "win_condition": "收集10颗星星",
            "lose_condition": "撞到滚石",
            "controls": "方向键移动",
            "suggestions": [],
            "confidence": "medium",
        },
    )

    update = generate_or_refine_plan(state)
    response = build_user_response(ConversationState(game_plan=update["game_plan"]))[
        "assistant_response"
    ]

    assert update["conversation_status"] == "ready_to_confirm"
    assert update["game_plan"]["introduction"]
    assert "小猫" in update["game_plan"]["introduction"]
    assert "星星" in update["game_plan"]["introduction"]
    assert response["card"]["introduction"] == update["game_plan"]["introduction"]


def test_user_provided_introduction_is_not_collected_before_plan_is_complete() -> None:
    state = ConversationState(
        user_event={
            "type": "chat",
            "message": "名字叫星星小猫，简介是帮助小猫收集星星，风格是可爱卡通。",
        },
    )

    update = generate_or_refine_plan(state)

    assert update["conversation_status"] == "collecting"
    assert update["game_plan"]["title"] == "星星小猫"
    assert update["game_plan"]["style"] == "可爱卡通"
    assert update["game_plan"]["introduction"] == ""

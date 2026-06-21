from agent.conversation_graph.nodes import (
    build_error_response,
    build_user_response,
    generate_or_refine_plan,
    ingest_user_event,
    lock_confirmation,
    regenerate_plan,
    update_material_usage,
    update_requirements,
)
from agent.state import ConversationState


def test_ingest_user_event_accepts_known_event_type() -> None:
    state = ConversationState(user_event={"type": "chat", "message": "做一个躲避障碍小游戏"})

    update = ingest_user_event(state)

    assert update["conversation_status"] == "collecting"
    assert update["handoff_to_generation"] is False
    assert update["assistant_response"]["suggestions"] == []


def test_ingest_user_event_marks_unknown_event_type_as_error() -> None:
    state = ConversationState(user_event={"type": "surprise"})

    update = ingest_user_event(state)

    assert update["conversation_status"] == "error"
    assert update["assistant_response"]["message"]


def test_skeleton_nodes_return_partial_state_updates() -> None:
    state = ConversationState(user_event={"type": "chat", "message": "做一个躲避障碍小游戏"})

    node_updates = [
        update_requirements(state),
        update_material_usage(state),
        generate_or_refine_plan(state),
        regenerate_plan(state),
        lock_confirmation(state),
        build_user_response(state),
        build_error_response(state),
    ]

    assert all(isinstance(update, dict) for update in node_updates)
    assert all("user_event" not in update for update in node_updates)
    assert any("assistant_response" in update for update in node_updates)


def test_update_requirements_merges_first_chat_message() -> None:
    state = ConversationState(
        user_event={
            "type": "chat",
            "message": "我想做一个可爱风格的躲避障碍小游戏，主角是一只小猫，要收集星星。",
        }
    )

    update = update_requirements(state)
    requirements = update["user_requirements"]

    assert "可爱风格" in requirements["intent_summary"]
    assert "躲避障碍" in requirements["must_have"]
    assert requirements["preference_profile"]["visual_style"] == "可爱"
    assert requirements["preference_profile"]["genre_candidates"]
    assert requirements["revision_count"] == 1


def test_update_requirements_keeps_existing_must_haves_when_user_adds_detail() -> None:
    state = ConversationState(
        user_requirements={
            **ConversationState().user_requirements,
            "intent_summary": "做一个躲避障碍小游戏",
            "must_have": ["躲避障碍"],
            "revision_count": 1,
        },
        user_event={"type": "chat", "message": "再加上收集星星，难度简单一点"},
    )

    update = update_requirements(state)
    requirements = update["user_requirements"]

    assert "躲避障碍" in requirements["must_have"]
    assert "收集星星" in requirements["must_have"]
    assert requirements["preference_profile"]["difficulty"] == "easy"
    assert requirements["revision_count"] == 2


def test_update_requirements_records_user_change_as_constraint() -> None:
    state = ConversationState(
        user_requirements={
            **ConversationState().user_requirements,
            "intent_summary": "做一个小猫躲避障碍游戏",
            "must_have": ["小猫主角", "躲避障碍"],
            "revision_count": 1,
        },
        user_event={"type": "chat", "message": "不要小猫了，改成小兔子主角"},
    )

    update = update_requirements(state)
    requirements = update["user_requirements"]

    assert "不要小猫了，改成小兔子主角" in requirements["constraints"]
    assert "小猫主角" in requirements["must_have"]
    assert requirements["revision_count"] == 2


def test_update_requirements_syncs_material_usage_when_chat_mentions_asset_use() -> None:
    state = ConversationState(
        material_usage={
            "assets": [
                {
                    "asset_id": "asset-1",
                    "filename": "forest.png",
                    "mime_type": "image/png",
                    "intended_use": "",
                }
            ]
        },
        user_event={"type": "chat", "message": "用这张背景图当森林背景"},
    )

    update = update_requirements(state)

    assert update["material_usage"]["assets"][0]["intended_use"] == "background"


def test_update_requirements_does_not_repeat_answered_open_questions() -> None:
    state = ConversationState(
        user_requirements={
            **ConversationState().user_requirements,
            "answered_questions": [
                {"question": "希望游戏是什么美术风格？", "answer": "可爱"}
            ],
        },
        user_event={"type": "chat", "message": "风格就是可爱一点"},
    )

    update = update_requirements(state)

    assert "希望游戏是什么美术风格？" not in update["user_requirements"]["open_questions"]


def test_build_user_response_with_incomplete_plan_asks_followup_without_card() -> None:
    state = ConversationState(
        game_plan={
            **ConversationState().game_plan,
            "title": "星星小猫",
            "introduction": "帮助小猫收集星星",
            "tags": ["arcade", "casual"],
            "gameplay": "躲避障碍并收集星星",
        }
    )

    update = build_user_response(state)
    response = update["assistant_response"]

    assert response["card"] is None
    assert response["actions"] == []
    assert response["message"]
    assert response["suggestions"] == []


def test_build_user_response_with_complete_plan_returns_card() -> None:
    state = ConversationState(
        game_plan={
            "plan_id": "plan-ready",
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
    )

    update = build_user_response(state)
    response = update["assistant_response"]

    assert response["card"]["title"] == "星星小猫"
    assert response["actions"] == ["generate", "regenerate"]

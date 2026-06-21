from agent.conversation_graph.nodes import build_user_response
from agent.conversation_graph.services.design_planner import DesignPlanner
from agent.conversation_graph.services.tone import friendly_design_message
from agent.providers import MockLLMProvider
from agent.state import ConversationState


def test_friendly_design_message_adds_single_contextual_icon() -> None:
    message = friendly_design_message(
        "我还需要确认核心玩法：玩家主要做什么？",
        missing_fields=["gameplay"],
    )

    assert message.startswith("🎮 ")
    assert message.count("🎮") == 1
    assert "先把核心玩法定下来" in message


def test_friendly_design_message_removes_extra_model_icons() -> None:
    message = friendly_design_message(
        "你的方向已经很清楚了✨ 现在只差一个关键点：你希望它是什么美术风格？",
        missing_fields=["style"],
        game_plan={"characters": ["小猫"]},
    )

    assert message.startswith("🎨 ")
    assert message.count("✨") == 0
    assert message.count("🎨") == 1
    assert "只差" not in message


def test_friendly_design_message_does_not_claim_one_step_when_many_fields_missing() -> None:
    message = friendly_design_message(
        "现在只差一个关键点：你希望它是什么美术风格？",
        missing_fields=["style", "characters", "win_condition", "lose_condition", "controls"],
        game_plan={"title": "星星小猫"},
    )

    assert "只差" not in message
    assert "星星小猫" in message
    assert "继续补齐几个关键设定" in message


def test_friendly_design_message_removes_one_question_claim_variants_when_many_fields_missing() -> None:
    message = friendly_design_message(
        "现在我只差一个最大关键的问题：你希望游戏是什么美术风格？",
        missing_fields=["style", "characters", "win_condition", "lose_condition", "controls"],
        game_plan={"title": "Q版魔法学院"},
    )

    assert "只差" not in message
    assert "最大关键的问题" not in message
    assert "最后" not in message
    assert "继续补齐几个关键设定" in message
    assert "Q版魔法学院" in message


def test_friendly_design_message_varies_opening_by_progress() -> None:
    early = friendly_design_message(
        "我还需要确认核心玩法：玩家主要做什么？",
        missing_fields=["gameplay", "style", "characters", "win_condition"],
    )
    late = friendly_design_message(
        "最后确认操作方式：玩家怎么控制？",
        missing_fields=["controls"],
        game_plan={"title": "星星小猫"},
    )

    assert "我已经抓到一些方向啦" not in early
    assert "我已经抓到一些方向啦" not in late
    assert early != late
    assert "最后确认" in late


def test_friendly_design_message_is_idempotent_for_generated_opening() -> None:
    message = friendly_design_message(
        "我们先把关键设定搭起来：你希望它是什么美术风格？",
        missing_fields=["style", "characters"],
    )

    assert message.count("我们先把关键设定搭起来") == 1
    assert message.count("🎨") == 1


def test_friendly_design_message_does_not_double_wrap_itself() -> None:
    once = friendly_design_message(
        "你这个“老鹰抓老鼠”的核心很清楚，抓捕追逐感已经有了 你希望它是什么美术风格？",
        missing_fields=["style", "win_condition"],
    )
    twice = friendly_design_message(
        once,
        missing_fields=["style", "win_condition"],
    )

    assert twice.count("我们先把关键设定搭起来") == 1
    assert twice.count("🎨") == 1


def test_friendly_design_message_removes_model_repeated_generated_opening() -> None:
    message = friendly_design_message(
        "我们先把关键设定搭起来：我们先把关键设定搭起来：像素风很适合这个题材，现在我只想确认一个关键点：你希望这款游戏更偏追逐躲避，还是带一点策略布置？",
        missing_fields=["win_condition", "lose_condition"],
    )

    assert message.count("我们先把关键设定搭起来") == 1
    assert "像素风很适合这个题材" in message


def test_build_user_response_uses_friendly_icon_for_followup() -> None:
    state = ConversationState(
        game_plan={
            **ConversationState().game_plan,
            "plan_id": "plan-cat",
            "title": "星星小猫",
        }
    )

    response = build_user_response(state)["assistant_response"]

    assert response["message"].startswith("🧩 ")
    assert "继续补齐几个关键设定" in response["message"]
    assert "简介" not in response["message"]
    assert all(isinstance(suggestion, str) for suggestion in response["suggestions"])


def test_build_user_response_uses_friendly_ready_message() -> None:
    state = ConversationState(
        game_plan={
            **ConversationState().game_plan,
            "plan_id": "plan-cat",
            "title": "星星小猫",
            "introduction": "帮助小猫收集星星并躲开滚石",
            "tags": ["arcade", "casual"],
            "gameplay": "躲避滚石并收集星星",
            "core_loop": ["躲避", "收集"],
            "style": "可爱卡通",
            "characters": ["小猫"],
            "win_condition": "收集10颗星星",
            "lose_condition": "撞到滚石",
            "controls": "方向键移动",
        }
    )

    response = build_user_response(state)["assistant_response"]

    assert response["message"].startswith("✨ ")
    assert "整理好一版完整方案" in response["message"]
    assert response["actions"] == ["generate", "regenerate"]


def test_design_planner_wraps_model_followup_with_friendly_tone() -> None:
    provider = MockLLMProvider(
        response={
            "game_plan_patch": {"title": "月光小猫"},
            "assistant_message": "你希望游戏是什么美术风格？",
            "suggestions": ["可爱卡通", "像素月夜"],
        }
    )

    update = DesignPlanner(provider=provider).plan(
        ConversationState(user_event={"type": "chat", "message": "做一个小猫游戏"})
    )

    message = update["assistant_response"]["message"]
    assert message.startswith("🎨 ")
    assert "小猫" in message

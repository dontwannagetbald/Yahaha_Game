import pytest
import json

from agent.conversation_graph.services.design_planner import DesignPlanner
from agent.conversation_graph.nodes._helpers import (
    MVP_TAGS,
    missing_confirmable_game_plan_fields,
)
from agent.providers import MockLLMProvider, ProviderError
from agent.state import ConversationState


class RecordingProvider(MockLLMProvider):
    def __init__(self, response: dict[str, object] | None = None) -> None:
        super().__init__(
            response=response
            or {
                "game_plan_patch": {},
                "assistant_message": "我已经理解大方向了。你希望先补充哪个关键设定？",
                "suggestions": ["先定游戏名字", "先定玩法目标", "先定操作方式"],
            }
        )
        self.messages = []

    def complete_json(self, *, messages, response_schema, temperature=0.2, max_tokens=1200):
        self.messages = messages
        return super().complete_json(
            messages=messages,
            response_schema=response_schema,
            temperature=temperature,
            max_tokens=max_tokens,
        )


def test_design_planner_allows_llm_to_complete_plan_on_first_turn() -> None:
    provider = MockLLMProvider(
        response={
            "game_plan_patch": {
                "title": "月光小猫",
                "introduction": "帮助小猫在月光森林收集星星",
                "tags": ["casual", "unknown", "arcade"],
                "gameplay": "躲避滚石并收集星星",
                "core_loop": ["移动", "躲避", "收集"],
                "style": "月光童话",
                "characters": ["小猫"],
                "win_condition": "收集10颗星星",
                "lose_condition": "撞到滚石",
                "controls": "方向键移动",
                "confidence": "high",
            },
            "suggestions": ["方向键移动", "收集10颗星星"],
        }
    )
    planner = DesignPlanner(provider=provider)
    state = ConversationState(
        user_event={"type": "chat", "message": "做一个小猫收集星星的游戏"},
    )

    update = planner.plan(state)

    assert update["conversation_status"] == "ready_to_confirm"
    assert update["game_plan"]["tags"] == ["casual", "arcade"]
    assert update["game_plan"]["suggestions"] == ["方向键移动", "收集10颗星星"]
    assert update["game_plan"]["title"] == "月光小猫"
    assert update["game_plan"]["win_condition"] == "收集10颗星星"
    assert "assistant_response" not in update


def test_design_planner_allows_overfill_after_question_budget() -> None:
    provider = MockLLMProvider(
        response={
            "game_plan_patch": {
                "title": "月光小猫",
                "tags": ["casual", "arcade"],
                "gameplay": "躲避滚石并收集星星",
                "core_loop": ["移动", "躲避", "收集"],
                "style": "月光童话",
                "characters": ["小猫"],
                "win_condition": "收集10颗星星",
                "lose_condition": "撞到滚石",
                "controls": "方向键移动",
            },
            "assistant_message": "",
            "suggestions": [],
        }
    )

    update = DesignPlanner(provider=provider).plan(
        ConversationState(
            user_requirements={
                **ConversationState().user_requirements,
                "revision_count": 6,
            },
            user_event={"type": "chat", "message": "做一个小猫收集星星的游戏"},
        )
    )

    assert update["conversation_status"] == "ready_to_confirm"
    assert update["game_plan"]["title"] == "月光小猫"
    assert update["game_plan"]["introduction"]


def test_design_planner_prompt_lists_mvp_tags_for_external_model() -> None:
    provider = RecordingProvider()

    DesignPlanner(provider=provider).plan(
        ConversationState(user_event={"type": "chat", "message": "做一个小游戏"})
    )

    system_prompt = provider.messages[0].content
    for tag in MVP_TAGS:
        assert tag in system_prompt


def test_design_planner_prompt_tells_model_not_to_reuse_previous_assistant_message() -> None:
    provider = RecordingProvider()

    DesignPlanner(provider=provider).plan(
        ConversationState(
            assistant_response={
                **ConversationState().assistant_response,
                "message": "🎨 我们先把关键设定搭起来：你希望它是什么美术风格？",
            },
            user_event={"type": "chat", "message": "像素风"},
        )
    )

    system_prompt = provider.messages[0].content
    user_payload = provider.messages[1].content
    assert "不要复用 previous_assistant_message" in system_prompt
    assert "previous_assistant_message" in user_payload
    assert "你希望它是什么美术风格？" in user_payload


def test_design_planner_prompt_includes_conversation_history() -> None:
    provider = RecordingProvider()

    DesignPlanner(provider=provider).plan(
        ConversationState(
            conversation_history=[
                {"role": "user", "content": "我想做一个魔法学院追逐游戏"},
                {"role": "assistant", "content": "你希望核心玩法是什么？"},
                {"role": "user", "content": "追着伏地魔跑图收集魔法碎片"},
            ],
            user_event={"type": "chat", "message": "画风要 Q 版魔法学院风"},
        )
    )

    system_prompt = provider.messages[0].content
    user_payload = json.loads(provider.messages[1].content)
    assert "conversation_history" in system_prompt
    assert user_payload["conversation_history"][-1] == {
        "role": "user",
        "content": "追着伏地魔跑图收集魔法碎片",
    }


def test_design_planner_absorbs_short_answer_to_previous_style_question() -> None:
    provider = MockLLMProvider(
        response={
            "game_plan_patch": {},
            "assistant_message": "这个风格很贴合商店扭蛋机。玩家怎样才算赢？",
            "suggestions": ["集齐一套潮玩", "获得稀有扭蛋", "完成顾客订单"],
        }
    )

    update = DesignPlanner(provider=provider).plan(
        ConversationState(
            game_plan={
                **ConversationState().game_plan,
                "plan_id": "plan-gacha",
                "title": "商店扭蛋机",
                "tags": ["casual", "simulation"],
                "gameplay": "在商店里操作扭蛋机收集潮玩",
                "core_loop": ["投币", "抽取", "收集"],
                "characters": ["玩家"],
            },
            assistant_response={
                **ConversationState().assistant_response,
                "message": "🎨 你希望它是什么美术风格？",
            },
            user_event={"type": "chat", "message": "可爱明亮的商店风"},
        )
    )

    assert update["game_plan"]["style"] == "可爱明亮的商店风"
    assert "style" not in missing_confirmable_game_plan_fields(update["game_plan"])
    assert "玩家怎样才算赢" in update["assistant_response"]["message"]


def test_design_planner_absorbs_short_answer_from_history_assistant_question() -> None:
    provider = MockLLMProvider(
        response={
            "game_plan_patch": {},
            "assistant_message": "像素风很适合追逐题材。玩家怎样才算赢？",
            "suggestions": ["抓到老鼠", "坚持到倒计时结束", "收集全部奶酪"],
        }
    )

    update = DesignPlanner(provider=provider).plan(
        ConversationState(
            game_plan={
                **ConversationState().game_plan,
                "plan_id": "plan-eagle",
                "title": "老鹰抓老鼠",
                "tags": ["arcade", "action"],
                "gameplay": "老鹰追逐老鼠并完成抓捕",
                "core_loop": ["追逐", "躲避", "抓捕"],
                "characters": ["老鹰", "老鼠"],
            },
            conversation_history=[
                {"role": "user", "content": "做一个老鹰抓老鼠"},
                {"role": "assistant", "content": "🎨 你希望它是什么视觉风格？"},
            ],
            user_event={"type": "chat", "message": "像素风"},
        )
    )

    assert update["game_plan"]["style"] == "像素风"
    assert "玩家怎样才算赢" in update["assistant_response"]["message"]


def test_design_planner_prompt_limits_followup_to_required_game_plan_fields() -> None:
    provider = RecordingProvider()

    DesignPlanner(provider=provider).plan(
        ConversationState(user_event={"type": "chat", "message": "做老鹰抓老鼠"})
    )

    system_prompt = provider.messages[0].content
    assert "assistant_message 只能追问缺失的必填 game_plan 字段" in system_prompt
    assert "不要追问特别能力" in system_prompt


def test_design_planner_prompt_asks_to_complete_plan_in_fewest_rounds() -> None:
    provider = RecordingProvider()

    DesignPlanner(provider=provider).plan(
        ConversationState(user_event={"type": "chat", "message": "做一个魔女冒险游戏"})
    )

    system_prompt = provider.messages[0].content
    assert "最短时间内补齐 game_plan" in system_prompt
    assert "优先选择一次能补齐最多缺失字段的问题" in system_prompt
    assert "suggestions 也要尽量覆盖多个缺失字段的组合答案" in system_prompt


def test_design_planner_prompt_uses_latest_fallback_game_plan_for_missing_fields() -> None:
    provider = RecordingProvider()

    DesignPlanner(provider=provider).plan(
        ConversationState(
            game_plan={
                **ConversationState().game_plan,
                "plan_id": "plan-witch",
                "tags": ["adventure", "roleplay"],
                "gameplay": "魔女学徒在学院里闯关并完成主线任务",
                "core_loop": ["闯关", "施法", "推进任务"],
                "characters": ["魔女学徒"],
                "win_condition": "完成主线任务并击败黑巫师",
            },
            assistant_response={
                **ConversationState().assistant_response,
                "message": "🎮 你希望它的具体操作和失败条件怎么定？",
            },
            user_event={"type": "chat", "message": "按键施法，生命值耗尽就失败"},
        )
    )

    user_payload = json.loads(provider.messages[1].content)
    assert user_payload["game_plan"]["controls"] == "按键施法"
    assert user_payload["game_plan"]["lose_condition"] == "生命值耗尽就失败"
    assert user_payload["missing_game_plan_fields"] == ["title", "style"]


def test_design_planner_prompt_prevents_similar_followups_and_prioritizes_title() -> None:
    provider = RecordingProvider()

    DesignPlanner(provider=provider).plan(
        ConversationState(
            game_plan={
                **ConversationState().game_plan,
                "plan_id": "plan-witch",
                "tags": ["adventure", "roleplay"],
                "gameplay": "魔女学徒闯关完成主线任务",
                "core_loop": ["闯关", "施法", "任务推进"],
                "style": "暗黑奇幻",
                "characters": ["学生巫师"],
                "win_condition": "完成主线任务并击败黑巫师",
                "lose_condition": "生命值耗尽",
                "controls": "按键施法",
            },
            conversation_history=[
                {"role": "assistant", "content": "主角是谁、怎么获胜，以及主要怎么操作？"},
                {"role": "user", "content": "学生巫师闯关，完成主线任务并击败黑巫师，按键施法"},
            ],
            user_event={"type": "chat", "message": "生命值耗尽就失败"},
        )
    )

    system_prompt = provider.messages[0].content
    user_payload = json.loads(provider.messages[1].content)
    assert "不要追问与 asked_game_plan_fields 语义相同或高度相似的问题" in system_prompt
    assert "title 在 missing_game_plan_fields 中" in system_prompt
    assert user_payload["asked_game_plan_fields"] == [
        "characters",
        "win_condition",
        "controls",
    ]
    assert user_payload["missing_game_plan_fields"] == ["title"]


def test_design_planner_prompt_exposes_missing_field_count_for_progress_claims() -> None:
    provider = RecordingProvider()

    DesignPlanner(provider=provider).plan(
        ConversationState(
            game_plan={
                **ConversationState().game_plan,
                "title": "Q版魔法学院",
                "tags": ["adventure", "casual"],
                "gameplay": "追着伏地魔跑图收集魔法碎片",
                "core_loop": ["追逐", "收集"],
            },
            user_event={"type": "chat", "message": "追着伏地魔跑图收集魔法碎片"},
        )
    )

    system_prompt = provider.messages[0].content
    user_payload = json.loads(provider.messages[1].content)
    assert "只有 missing_field_count 等于 1" in system_prompt
    assert user_payload["missing_field_count"] > 1
    assert user_payload["missing_game_plan_fields"] == [
        "style",
        "characters",
        "win_condition",
        "lose_condition",
        "controls",
    ]


def test_design_planner_prompt_forces_completion_after_five_question_rounds() -> None:
    provider = RecordingProvider(
        response={
            "game_plan_patch": {
                "style": "像素街机",
                "characters": ["老鹰", "老鼠"],
                "win_condition": "老鹰在倒计时结束前抓到老鼠",
                "lose_condition": "倒计时结束仍未抓到老鼠",
                "controls": "方向键移动老鹰",
            },
            "assistant_message": "",
            "suggestions": [],
        }
    )

    DesignPlanner(provider=provider).plan(
        ConversationState(
            user_requirements={
                **ConversationState().user_requirements,
                "revision_count": 6,
            },
            game_plan={
                **ConversationState().game_plan,
                "plan_id": "plan-eagle",
                "title": "老鹰抓老鼠",
                "tags": ["arcade"],
                "gameplay": "老鹰追逐老鼠并完成抓捕",
                "core_loop": ["追逐", "躲避", "抓捕"],
            },
            user_event={"type": "chat", "message": "随便你补全吧"},
        )
    )

    system_prompt = provider.messages[0].content
    user_payload = json.loads(provider.messages[1].content)
    assert "should_force_complete_plan 为 true" in system_prompt
    assert user_payload["max_question_rounds"] == 5
    assert user_payload["design_chat_round"] == 6
    assert user_payload["should_force_complete_plan"] is True


def test_design_planner_generates_card_after_five_question_rounds() -> None:
    provider = MockLLMProvider(
        response={
            "game_plan_patch": {
                "style": "明亮卡通",
                "characters": ["老鹰", "老鼠"],
                "win_condition": "老鹰在倒计时结束前抓到老鼠",
                "lose_condition": "倒计时结束仍未抓到老鼠",
                "controls": "方向键移动老鹰",
            },
            "assistant_message": "",
            "suggestions": [],
        }
    )

    update = DesignPlanner(provider=provider).plan(
        ConversationState(
            user_requirements={
                **ConversationState().user_requirements,
                "intent_summary": "用户想做一个老鹰抓老鼠的追逐小游戏。",
                "revision_count": 6,
            },
            game_plan={
                **ConversationState().game_plan,
                "plan_id": "plan-eagle",
                "title": "老鹰抓老鼠",
                "tags": ["arcade", "action"],
                "gameplay": "老鹰追逐老鼠并完成抓捕",
                "core_loop": ["追逐", "躲避", "抓捕"],
            },
            user_event={"type": "chat", "message": "你帮我定吧"},
        )
    )

    assert update["conversation_status"] == "ready_to_confirm"
    assert missing_confirmable_game_plan_fields(update["game_plan"]) == []
    assert update["game_plan"]["introduction"]
    assert "assistant_response" not in update


def test_design_planner_raises_after_max_rounds_if_model_omits_fields() -> None:
    provider = MockLLMProvider(
        response={
            "game_plan_patch": {"tags": ["arcade", "casual"]},
            "assistant_message": "",
            "suggestions": [],
        }
    )

    with pytest.raises(ProviderError, match="did not complete game_plan") as exc_info:
        DesignPlanner(provider=provider).plan(
            ConversationState(
                user_requirements={
                    **ConversationState().user_requirements,
                    "intent_summary": "用户想做一个老鹰抓老鼠的追逐小游戏。",
                    "must_have": ["老鹰主角", "追逐老鼠"],
                    "revision_count": 6,
                },
                game_plan={
                    **ConversationState().game_plan,
                    "plan_id": "plan-eagle",
                    "title": "老鹰抓老鼠",
                    "tags": ["arcade"],
                    "gameplay": "老鹰追逐老鼠并完成抓捕",
                    "core_loop": ["追逐", "躲避", "抓捕"],
                },
                user_event={"type": "chat", "message": "你直接补齐方案"},
            )
        )

    assert exc_info.value.details["reason"] == "incomplete_forced_completion"
    assert "style" in exc_info.value.details["missing_fields"]


def test_design_planner_raises_when_provider_fails() -> None:
    provider = MockLLMProvider(raises=RuntimeError("provider unavailable"))
    planner = DesignPlanner(provider=provider)
    state = ConversationState(
        user_requirements={
            **ConversationState().user_requirements,
            "preference_profile": {
                **ConversationState().user_requirements["preference_profile"],
                "genre_candidates": ["arcade", "unknown"],
            },
        },
        user_event={
            "type": "chat",
            "message": "我想做一个小猫躲避障碍的轻松小游戏。",
        },
    )

    with pytest.raises(ProviderError, match="provider unavailable"):
        planner.plan(state)


def test_design_planner_raises_when_collecting_response_has_no_model_suggestions() -> None:
    provider = MockLLMProvider(
        response={
            "game_plan_patch": {"title": "云朵快跑"},
            "assistant_message": "你希望它是什么视觉风格？",
            "suggestions": [],
        }
    )

    with pytest.raises(ProviderError, match="empty suggestions") as exc_info:
        DesignPlanner(provider=provider).plan(
            ConversationState(user_event={"type": "chat", "message": "做一个云朵游戏"})
        )

    assert exc_info.value.details["reason"] == "empty_suggestions"


def test_design_planner_raises_when_collecting_response_has_no_question_or_suggestions() -> None:
    provider = MockLLMProvider(
        response={
            "game_plan_patch": {"gameplay": "老鹰追逐老鼠并完成抓捕"},
            "assistant_message": "",
            "suggestions": [],
        }
    )

    with pytest.raises(ProviderError, match="empty assistant_message") as exc_info:
        DesignPlanner(provider=provider).plan(
            ConversationState(user_event={"type": "chat", "message": "做一个老鹰抓老鼠"})
        )

    assert exc_info.value.details["reason"] == "empty_assistant_message"


def test_design_planner_partial_llm_plan_keeps_collecting_with_custom_followup() -> None:
    provider = MockLLMProvider(
        response={
            "game_plan_patch": {
                "title": "云朵快跑",
                "introduction": "在云朵间躲避风暴并收集光点",
                "tags": ["arcade", "casual"],
                "gameplay": "左右移动躲避风暴并收集光点",
                "core_loop": ["移动", "躲避", "收集"],
            },
            "assistant_message": "这个方向不错。你希望它是什么视觉风格？",
            "suggestions": ["梦幻卡通", "像素天空", "霓虹街机"],
        }
    )
    planner = DesignPlanner(provider=provider)

    update = planner.plan(
        ConversationState(
            user_event={"type": "chat", "message": "做一个云朵跑酷收集游戏"}
        )
    )

    assert update["conversation_status"] == "collecting"
    assert update["assistant_response"]["message"].startswith("🎨 ")
    assert "这个方向不错。你希望它是什么视觉风格？" in update["assistant_response"]["message"]
    assert update["assistant_response"]["suggestions"] == ["梦幻卡通", "像素天空", "霓虹街机"]


def test_design_planner_second_turn_can_complete_plan_from_existing_state() -> None:
    provider = MockLLMProvider(
        response={
            "game_plan_patch": {
                "style": "梦幻卡通",
                "characters": ["云朵精灵"],
                "win_condition": "收集20个光点",
                "lose_condition": "被风暴追上",
                "controls": "方向键移动",
            },
            "assistant_message": "风格和主角都明确了。玩家怎样才算赢、怎样算失败，主要怎么操作？",
            "suggestions": ["收集20个光点，被风暴追上失败，方向键移动"],
        }
    )
    planner = DesignPlanner(provider=provider)
    state = ConversationState(
        game_plan={
            **ConversationState().game_plan,
            "plan_id": "plan-cloud",
            "title": "云朵快跑",
            "introduction": "在云朵间躲避风暴并收集光点",
            "tags": ["arcade", "casual"],
            "gameplay": "左右移动躲避风暴并收集光点",
            "core_loop": ["移动", "躲避", "收集"],
        },
        user_event={"type": "chat", "message": "梦幻卡通，主角是云朵精灵"},
    )

    update = planner.plan(state)

    assert update["conversation_status"] == "ready_to_confirm"
    assert update["game_plan"]["characters"] == ["云朵精灵"]
    assert update["game_plan"]["win_condition"] == "收集20个光点"
    assert "assistant_response" not in update


def test_design_planner_derives_core_loop_from_gameplay_when_model_omits_it() -> None:
    provider = MockLLMProvider(
        response={
            "game_plan_patch": {"tags": ["arcade", "casual"]},
            "assistant_message": "",
            "suggestions": [],
        }
    )
    planner = DesignPlanner(provider=provider)

    update = planner.plan(
        ConversationState(
            user_event={
                "type": "chat",
                "message": (
                    "名字叫星星小猫，玩法是躲避滚石并收集星星，"
                    "风格是可爱卡通，主角是小猫，胜利条件是收集10颗星星，"
                    "失败条件是撞到滚石，操作方式是方向键移动"
                ),
            }
        )
    )

    assert update["conversation_status"] == "ready_to_confirm"
    assert update["game_plan"]["core_loop"] == ["躲避", "收集"]

import json
from importlib import import_module

from agent.conversation_graph.nodes.regenerate_plan import regenerate_plan
from agent.conversation_graph.services.regenerate_planner import RegeneratePlanner
from agent.providers import MockLLMProvider
from agent.state import ConversationState


def _ready_state() -> ConversationState:
    return ConversationState(
        user_requirements={
            **ConversationState().user_requirements,
            "intent_summary": "做一个学生巫师闯关击败黑巫师的魔法对战游戏",
            "constraints": ["节奏紧凑"],
        },
        game_plan={
            **ConversationState().game_plan,
            "plan_id": "plan-witch",
            "title": "魔法闯关",
            "introduction": "学生巫师在学院中闯关并击败黑巫师。",
            "tags": ["adventure", "roleplay"],
            "gameplay": "学生巫师闯关完成主线任务",
            "core_loop": ["闯关", "施法", "任务推进"],
            "style": "暗黑奇幻",
            "characters": ["学生巫师"],
            "win_condition": "完成主线任务并击败黑巫师",
            "lose_condition": "生命值耗尽",
            "controls": "按键施法",
            "confidence": "medium",
        },
        material_usage={
            "assets": [
                {"asset_id": "asset-1", "filename": "wizard.png", "mime_type": "image/png"}
            ]
        },
        user_event={"type": "regenerate"},
    )


def test_regenerate_planner_uses_llm_card_variant_and_preserves_core_plan() -> None:
    provider = MockLLMProvider(
        response={
            "title": "黑巫师试炼",
            "introduction": "学生巫师踏入暗黑学院试炼，用按键施法推进主线任务，并在生命耗尽前击败黑巫师。",
            "tags": ["adventure", "roleplay"],
        }
    )

    update = RegeneratePlanner(provider=provider).regenerate(_ready_state())

    assert provider.calls
    assert update["conversation_status"] == "ready_to_confirm"
    assert update["game_plan"]["title"] == "黑巫师试炼"
    assert update["game_plan"]["introduction"].startswith("学生巫师踏入暗黑学院")
    assert update["game_plan"]["tags"] == ["adventure", "roleplay"]
    assert update["game_plan"]["gameplay"] == "学生巫师闯关完成主线任务"
    assert update["game_plan"]["win_condition"] == "完成主线任务并击败黑巫师"
    assert update["game_plan"]["controls"] == "按键施法"


def test_regenerate_planner_prompt_requires_consistent_but_different_card() -> None:
    provider = MockLLMProvider(
        response={
            "title": "黑巫师试炼",
            "introduction": "学生巫师踏入暗黑学院试炼，用按键施法推进主线任务，并在生命耗尽前击败黑巫师。",
            "tags": ["adventure", "roleplay"],
        }
    )

    RegeneratePlanner(provider=provider).regenerate(_ready_state())

    system_prompt = provider.calls[0]["messages"][0].content
    user_payload = json.loads(provider.calls[0]["messages"][1].content)
    assert "重新生成一版确认卡片" in system_prompt
    assert "不要修改玩法、角色、胜负条件、操作方式或素材用途" in system_prompt
    assert "title、introduction、tags" in system_prompt
    assert user_payload["current_card"]["title"] == "魔法闯关"
    assert user_payload["game_plan"]["win_condition"] == "完成主线任务并击败黑巫师"


def test_regenerate_plan_node_calls_configured_provider(monkeypatch) -> None:
    planner_module = import_module("agent.conversation_graph.services.regenerate_planner")
    provider = MockLLMProvider(
        response={
            "title": "黑巫师试炼",
            "introduction": "学生巫师踏入暗黑学院试炼，用按键施法推进主线任务，并在生命耗尽前击败黑巫师。",
            "tags": ["adventure", "roleplay"],
        }
    )

    monkeypatch.setattr(planner_module, "provider_from_env", lambda: provider)

    update = regenerate_plan(_ready_state())

    assert provider.calls
    assert update["game_plan"]["title"] == "黑巫师试炼"

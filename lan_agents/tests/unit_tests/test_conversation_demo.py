from agent.conversation_graph.demo import (
    DEFAULT_DEMO_USER_MESSAGES,
    pretty_print_messages,
    run_conversation_demo,
)


class FakeConversationGraph:
    def __init__(self) -> None:
        self.calls = 0

    def invoke(self, state):
        self.calls += 1
        if self.calls == 1:
            return {
                **state,
                "conversation_status": "collecting",
                "assistant_response": {
                    "message": "希望游戏是什么美术风格？",
                    "suggestions": ["可爱卡通", "像素风"],
                    "card": None,
                    "actions": [],
                },
                "game_plan": {
                    **state.get("game_plan", {}),
                    "plan_id": "plan-demo",
                    "tags": ["arcade", "casual"],
                    "gameplay": "躲避滚石并收集星星",
                },
            }
        return {
            **state,
            "conversation_status": "ready_to_confirm",
            "assistant_response": {
                "message": "我整理好了一版完整方案，你可以生成，也可以换一换。",
                "suggestions": [],
                "card": {
                    "plan_id": "plan-demo",
                    "title": "星星小猫",
                    "introduction": "帮助小猫收集星星并躲避滚石。",
                    "tags": ["arcade", "casual"],
                },
                "actions": ["generate", "regenerate"],
            },
            "game_plan": {
                "plan_id": "plan-demo",
                "title": "星星小猫",
                "introduction": "帮助小猫收集星星并躲避滚石。",
                "tags": ["arcade", "casual"],
                "gameplay": "躲避滚石并收集星星",
                "core_loop": ["移动", "躲避", "收集"],
                "style": "可爱卡通",
                "characters": ["小猫"],
                "win_condition": "收集10颗星星",
                "lose_condition": "撞到滚石",
                "controls": "方向键移动",
                "suggestions": [],
                "confidence": "medium",
            },
        }


def test_pretty_print_messages_includes_dialog_and_card() -> None:
    output = pretty_print_messages(
        [
            {"role": "user", "content": "做一个小猫游戏"},
            {
                "role": "assistant",
                "content": "希望游戏是什么美术风格？",
                "suggestions": ["可爱卡通"],
            },
            {
                "role": "card",
                "content": {
                    "title": "星星小猫",
                    "introduction": "帮助小猫收集星星。",
                    "tags": ["arcade"],
                },
            },
        ]
    )

    assert "[User] 做一个小猫游戏" in output
    assert "[Assistant] 希望游戏是什么美术风格？" in output
    assert "建议：可爱卡通" in output
    assert "[Card] 星星小猫" in output


def test_run_conversation_demo_collects_logs_and_final_card() -> None:
    result = run_conversation_demo(
        graph=FakeConversationGraph(),
        user_messages=DEFAULT_DEMO_USER_MESSAGES[:2],
    )

    assert result["final_state"]["conversation_status"] == "ready_to_confirm"
    assert result["final_card"]["title"] == "星星小猫"
    assert result["agent_logs"][0]["step"] == "conversation_turn_1"
    assert result["agent_logs"][1]["status"] == "ready_to_confirm"
    assert "[Agent Logs]" in result["output"]
    assert "[Final Game Plan]" in result["output"]

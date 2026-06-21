from importlib import import_module

from agent.providers.mock import MockLLMProvider
from agent.revision_graph.nodes.understand_revision_intent import understand_revision_intent
from agent.revision_graph.services.revision_planner import RevisionPlanner
from agent.revision_graph.state import RevisionState


def _revision_state(message: str = "把主角换成兔子，背景改成雪地") -> RevisionState:
    return RevisionState(
        parent_job={"id": "job-parent-1", "status": "succeeded"},
        base_game_plan={
            "plan_id": "plan-parent",
            "title": "Forest Runner",
            "style": "bright forest",
            "characters": ["fox"],
            "lose_condition": "Hit one rock.",
        },
        base_material_usage={"assets": []},
        generated_result={"artifact_prefix": "drafts/user-1/job-parent-1/v1"},
        user_message=message,
    )


def test_revision_planner_uses_llm_provider_for_clear_patch() -> None:
    provider = MockLLMProvider(
        response={
            "revision_intent": "把主角改成兔子并切换雪地背景",
            "game_plan_patch": {"characters": ["兔子"], "style": "雪地场景"},
            "requires_regeneration": True,
            "assistant_message": "我会把主角和背景一起换掉，生成一个新版本。",
            "suggestions": [],
        }
    )

    update = RevisionPlanner(provider=provider).plan(_revision_state())

    assert provider.calls
    system_prompt = provider.calls[0]["messages"][0].content
    assert "生成后修改" in system_prompt
    assert "不覆盖旧产物" in system_prompt
    assert update["revision_status"] == "clear"
    assert update["revision_intent"] == "把主角改成兔子并切换雪地背景"
    assert update["game_plan_patch"] == {"characters": ["兔子"], "style": "雪地场景"}
    assert update["requires_regeneration"] is True
    assert update["assistant_response"]["message"] == "我会把主角和背景一起换掉，生成一个新版本。"


def test_understand_revision_intent_node_calls_configured_revision_planner(monkeypatch) -> None:
    planner_module = import_module("agent.revision_graph.services.revision_planner")

    class FakePlanner:
        def plan(self, state):
            return {
                "revision_status": "clear",
                "revision_intent": "降低难度",
                "game_plan_patch": {"lose_condition": "失败条件更宽松"},
                "requires_regeneration": True,
            }

    monkeypatch.setattr(planner_module, "RevisionPlanner", lambda: FakePlanner())

    update = understand_revision_intent(_revision_state("降低难度"))

    assert update["revision_status"] == "clear"
    assert update["game_plan_patch"]["lose_condition"] == "失败条件更宽松"

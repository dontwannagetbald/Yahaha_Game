import pytest

from agent import revision_graph

pytestmark = pytest.mark.anyio


def _base_revision_input(message: str) -> dict:
    return {
        "parent_job": {
            "id": "job-parent-1",
            "status": "succeeded",
            "artifact_prefix": "drafts/user-1/job-parent-1/v1",
        },
        "base_game_plan": {
            "plan_id": "plan-parent",
            "title": "Forest Runner",
            "introduction": "A fast forest dodge game.",
            "tags": ["arcade", "runner"],
            "gameplay": "Move left and right to dodge rocks and collect stars.",
            "core_loop": ["dodge", "collect", "survive"],
            "style": "bright forest",
            "characters": ["fox"],
            "win_condition": "Collect 20 stars.",
            "lose_condition": "Hit one rock.",
            "controls": "Arrow keys move.",
            "suggestions": [],
            "confidence": "high",
        },
        "base_material_usage": {
            "assets": [
                {
                    "asset_id": "asset-forest-video",
                    "filename": "forest.mp4",
                    "mime_type": "video/mp4",
                    "purpose": "background reference",
                }
            ]
        },
        "generated_result": {
            "artifact_prefix": "drafts/user-1/job-parent-1/v1",
            "manifest_path": "drafts/user-1/job-parent-1/v1/manifest.json",
            "entry_path": "drafts/user-1/job-parent-1/v1/index.html",
        },
        "user_message": message,
    }


async def test_revision_graph_creates_revision_job_payload_for_clear_change() -> None:
    revision_input = _base_revision_input("把失败条件改宽松一点，碰到障碍后扣血，血量归零才失败。")

    result = await revision_graph.ainvoke(revision_input)

    assert result["revision_status"] == "ready_to_generate"
    assert result["requires_regeneration"] is True
    assert "失败条件" in result["revision_intent"]
    assert result["game_plan_patch"]["lose_condition"] == "碰到障碍后扣血，血量归零才失败"
    assert result["revision_job_payload"]["parent_job_id"] == "job-parent-1"
    assert result["revision_job_payload"]["revision_intent"] == result["revision_intent"]
    assert result["revision_job_payload"]["game_plan"]["lose_condition"] == "碰到障碍后扣血，血量归零才失败"
    assert result["revision_job_payload"]["material_usage"]["assets"][0]["asset_id"] == "asset-forest-video"
    assert result["revision_job_payload"]["generated_result"]["artifact_prefix"] == "drafts/user-1/job-parent-1/v1"
    assert revision_input["base_game_plan"]["lose_condition"] == "Hit one rock."
    assert result["assistant_response"]["actions"] == ["create_revision_job"]


async def test_revision_graph_asks_clarifying_question_for_unclear_change() -> None:
    result = await revision_graph.ainvoke(_base_revision_input("改得更好玩一点"))

    assert result["revision_status"] == "needs_clarification"
    assert result["requires_regeneration"] is False
    assert result["game_plan_patch"] == {}
    assert result["revision_job_payload"] == {}
    assert result["assistant_response"]["actions"] == []
    assert result["assistant_response"]["suggestions"]


async def test_revision_graph_redacts_sensitive_fragments_from_outputs() -> None:
    result = await revision_graph.ainvoke(
        _base_revision_input("把背景改成雪地，token=abc123，X-Amz-Signature=secret")
    )

    rendered = str(
        {
            "revision_intent": result["revision_intent"],
            "game_plan_patch": result["game_plan_patch"],
            "assistant_response": result["assistant_response"],
            "agent_logs": result["agent_logs"],
        }
    )
    assert "abc123" not in rendered
    assert "X-Amz-Signature" not in rendered
    assert "secret" not in rendered.lower()

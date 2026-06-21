from langgraph.pregel import Pregel

from agent.graph import graph, revision_graph
from agent.state import ConversationState
from agent.revision_graph.state import RevisionState


def test_placeholder() -> None:
    # TODO: You can add actual unit tests
    # for your graph and other logic here.
    assert isinstance(graph, Pregel)
    assert isinstance(revision_graph, Pregel)


def test_conversation_state_defaults_include_phase_one_contract() -> None:
    state = ConversationState(user_event={"type": "chat", "message": "做一个躲避障碍的小游戏"})

    assert state.user_requirements["intent_summary"] == ""
    assert state.user_requirements["must_have"] == []
    assert state.game_plan["tags"] == []
    assert state.material_usage == {"assets": []}
    assert state.assistant_response["suggestions"] == []
    assert state.handoff_to_generation is False
    assert state.conversation_status == "collecting"


def test_revision_state_defaults_include_post_generation_contract() -> None:
    state = RevisionState(user_message="降低难度")

    assert state.parent_job == {}
    assert state.base_game_plan == {}
    assert state.base_material_usage == {"assets": []}
    assert state.generated_result == {}
    assert state.revision_intent == ""
    assert state.game_plan_patch == {}
    assert state.requires_regeneration is False
    assert state.revision_job_payload == {}
    assert state.assistant_response["actions"] == []
    assert state.revision_status == "understanding"
